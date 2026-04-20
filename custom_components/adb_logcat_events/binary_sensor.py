"""Capteur binaire diagnostique pour l'état de connexion ADB."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_CONNECTION_STATE
from .logcat_listener import ShieldLogcatListener


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    listener: ShieldLogcatListener = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ConnectionStatusSensor(entry, listener)])


class ConnectionStatusSensor(BinarySensorEntity):
    """Indique si la connexion ADB est active."""

    _attr_has_entity_name = True
    _attr_translation_key = "connection_status"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: ConfigEntry, listener: ShieldLogcatListener) -> None:
        self._entry = entry
        self._listener = listener
        self._attr_unique_id = f"{entry.entry_id}_connection_status"
        self._attr_is_on = listener.connected
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data["name"],
            manufacturer="NVIDIA",
            model="Shield TV",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_CONNECTION_STATE.format(entry_id=self._entry.entry_id),
                self._handle_state_update,
            )
        )

    @callback
    def _handle_state_update(self, connected: bool) -> None:
        self._attr_is_on = connected
        self.async_write_ha_state()
