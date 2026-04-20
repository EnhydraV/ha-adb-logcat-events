"""Bouton de reconnexion forcée pour ADB Logcat Events."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .logcat_listener import ShieldLogcatListener


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    listener: ShieldLogcatListener = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ReconnectButton(entry, listener)])


class ReconnectButton(ButtonEntity):
    """Bouton permettant de forcer la reconnexion ADB."""

    _attr_has_entity_name = True
    _attr_translation_key = "reconnect"

    def __init__(self, entry: ConfigEntry, listener: ShieldLogcatListener) -> None:
        self._entry = entry
        self._listener = listener
        self._attr_unique_id = f"{entry.entry_id}_reconnect"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data["name"],
            manufacturer="NVIDIA",
            model="Shield TV",
        )

    async def async_press(self) -> None:
        """Arrête le listener en cours et en démarre un nouveau."""
        await self._listener.async_stop()
        await self._listener.async_start()
