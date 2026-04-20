"""ADB Logcat Events — Home Assistant custom component."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant

from .const import DEFAULT_PORT, DOMAIN
from .logcat_listener import ShieldLogcatListener

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor", "button"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Global domain setup."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Start the ADB listener for this config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    name = entry.data[CONF_NAME]

    listener = ShieldLogcatListener(
        hass=hass,
        entry_id=entry.entry_id,
        host=host,
        port=port,
        name=name,
    )

    hass.data[DOMAIN][entry.entry_id] = listener
    await listener.async_start()

    entry.async_on_unload(listener.async_stop)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Stop the ADB listener when the entry is removed."""
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    listener: ShieldLogcatListener = hass.data[DOMAIN].pop(entry.entry_id, None)
    if listener:
        await listener.async_stop()
    return True
