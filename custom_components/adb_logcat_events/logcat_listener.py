"""ADB logcat listener to capture Shield TV volume button events."""
from __future__ import annotations

import asyncio
import logging

from adb_shell.adb_device_async import AdbDeviceTcpAsync
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.auth.keygen import keygen

from .const import (
    BACKOFF_INITIAL,
    BACKOFF_MAX,
    BACKOFF_MULTIPLIER,
    DOMAIN,
    EVENT_VOLUME_BUTTON,
    LOGCAT_PATTERNS,
)

_LOGGER = logging.getLogger(__name__)

ADB_KEY_PATH = "/config/.storage/adb_logcat_events_adb_key"


def _get_signer() -> PythonRSASigner:
    """Load or generate the persistent ADB key."""
    try:
        with open(ADB_KEY_PATH, "rb") as f:
            private = f.read()
        with open(ADB_KEY_PATH + ".pub", "rb") as f:
            public = f.read()
    except FileNotFoundError:
        _LOGGER.info("Generating a new ADB key for adb_logcat_events")
        keygen(ADB_KEY_PATH)
        with open(ADB_KEY_PATH, "rb") as f:
            private = f.read()
        with open(ADB_KEY_PATH + ".pub", "rb") as f:
            public = f.read()

    return PythonRSASigner(public, private)


class ShieldLogcatListener:
    """Manages the ADB connection and logcat streaming for a Shield TV."""

    def __init__(self, hass, entry_id: str, host: str, port: int, name: str) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.host = host
        self.port = port
        self.name = name
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    async def async_start(self) -> None:
        """Start the background listening task."""
        self._stop_event.clear()
        self._task = self.hass.loop.create_task(
            self._listen_loop(), name=f"adb_logcat_events_{self.entry_id}"
        )
        _LOGGER.info("ADB Logcat Events: starting listener for %s (%s:%s)", self.name, self.host, self.port)

    async def async_stop(self) -> None:
        """Gracefully stop the task."""
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        _LOGGER.info("ADB Logcat Events: listener stopped for %s", self.name)

    async def _listen_loop(self) -> None:
        """Main loop with reconnection and exponential backoff."""
        backoff = BACKOFF_INITIAL

        while not self._stop_event.is_set():
            try:
                await self._connect_and_stream()
                # Stream ended normally → reset backoff
                backoff = BACKOFF_INITIAL

            except asyncio.CancelledError:
                return

            except Exception as exc:
                _LOGGER.warning(
                    "ADB Logcat Events: error on %s: %s. Reconnecting in %ds.",
                    self.name, exc, backoff
                )

            if self._stop_event.is_set():
                return

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=backoff)
            except asyncio.TimeoutError:
                pass

            backoff = min(backoff * BACKOFF_MULTIPLIER, BACKOFF_MAX)

    async def _connect_and_stream(self) -> None:
        """Open the ADB connection and stream logcat output."""
        signer = await self.hass.async_add_executor_job(_get_signer)
        device = AdbDeviceTcpAsync(self.host, self.port, default_timeout_s=10.0)

        try:
            await device.connect(rsa_keys=[signer], auth_timeout_s=10.0)
            _LOGGER.info("ADB Logcat Events: connected to %s", self.name)

            # Flush existing logcat, listen to new lines only.
            # Filter on WindowManager to reduce data volume.
            async for line in device.streaming_shell(
                    "logcat -v brief -T 1 WindowManager:V *:S"
            ):
                if self._stop_event.is_set():
                    break

                line = line.strip()
                if not line:
                    continue

                for pattern, action in LOGCAT_PATTERNS.items():
                    if pattern in line:
                        _LOGGER.debug("ADB Logcat Events: %s → %s", self.name, action)
                        self.hass.bus.async_fire(
                            EVENT_VOLUME_BUTTON,
                            {
                                "device_name": self.name,
                                "entry_id": self.entry_id,
                                "action": action,
                            },
                        )
                        break

        finally:
            try:
                await device.close()
            except Exception:
                pass
