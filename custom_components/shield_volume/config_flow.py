"""Config flow for ADB Logcat Events."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant

from adb_shell.adb_device_async import AdbDeviceTcpAsync
from adb_shell.auth.sign_pythonrsa import PythonRSASigner

from .const import DEFAULT_PORT, DOMAIN
from .logcat_listener import _get_signer

_LOGGER = logging.getLogger(__name__)


async def _test_connection(hass: HomeAssistant, host: str, port: int) -> str | None:
    """Attempt an ADB connection. Returns None on success, otherwise an error code."""
    try:
        signer = await hass.async_add_executor_job(_get_signer)
        device = AdbDeviceTcpAsync(host, port, default_timeout_s=10.0)
        connected = await device.connect(rsa_keys=[signer], auth_timeout_s=15.0)
        await device.close()
        if not connected:
            return "auth_failed"
        return None
    except ConnectionRefusedError:
        return "cannot_connect"
    except TimeoutError:
        return "cannot_connect"
    except Exception as exc:
        _LOGGER.exception("Unexpected error during connection test: %s", exc)
        return "unknown"


class ShieldVolumeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the ADB Logcat Events config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            name = user_input[CONF_NAME]

            # Prevent configuring the same host:port twice
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            error = await _test_connection(self.hass, host, port)
            if error is None:
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_NAME: name,
                        CONF_HOST: host,
                        CONF_PORT: port,
                    },
                )
            errors["base"] = error

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Shield TV Living Room"): str,
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
