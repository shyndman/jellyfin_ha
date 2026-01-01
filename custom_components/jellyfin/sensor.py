"""Support to interface with the Jellyfin API."""
import logging
from typing import TYPE_CHECKING

from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    CONF_URL,
    DEVICE_DEFAULT_NAME,
    STATE_ON,
    STATE_OFF,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import JellyfinClientManager, autolog

from .const import (
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

PLATFORM = "sensor"

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: "AddEntitiesCallback",
) -> None:

    _jelly: JellyfinClientManager = hass.data[DOMAIN][config_entry.data.get(CONF_URL)]["manager"]
    async_add_entities([JellyfinSensor(_jelly)], True)
    

class JellyfinSensor(Entity):
    """Representation of an Jellyfin device."""

    def __init__(self, jelly_cm: JellyfinClientManager):
        """Initialize the Jellyfin device."""
        _LOGGER.debug("New Jellyfin Sensor initialized")
        self.jelly_cm = jelly_cm
        self._available = True

    async def async_added_to_hass(self) -> None:
        autolog("<<<")
        self.hass.data[DOMAIN][self.jelly_cm.host][PLATFORM]["entities"].append(self)

    async def async_will_remove_from_hass(self) -> None:
        autolog("<<<")
        self.hass.data[DOMAIN][self.jelly_cm.host][PLATFORM]["entities"].remove(self)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.jelly_cm.is_available

    @property
    def unique_id(self) -> str | None:
        """Return the id of this jellyfin server."""
        info = self.jelly_cm.info
        if info is None:
            return None
        return info["Id"]

    @property
    def device_info(self) -> dict[str, object] | None:
        """Return device information about this entity."""
        info = self.jelly_cm.info
        if info is None:
            return None
        return {
            "identifiers": {
                # Unique identifiers within a specific domain
                (DOMAIN, self.jelly_cm.server_url)
            },
            "manufacturer": "Jellyfin",
            "model": f"Jellyfin {info['Version']}".rstrip(),
            "name": info['ServerName'],
            "configuration_url": self.jelly_cm.server_url,
        }

    @property
    def name(self) -> str:
        """Return the name of the device."""
        info = self.jelly_cm.info
        if info is None:
            return DEVICE_DEFAULT_NAME
        return f"Jellyfin {info['ServerName']}" or DEVICE_DEFAULT_NAME

    @property
    def should_poll(self) -> bool:
        """Return True if entity has to be polled for state."""
        return False

    @property
    def state(self) -> str:
        """Return the state of the device."""
        return STATE_ON if self.jelly_cm.is_available else STATE_OFF

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        """Return the state attributes."""
        info = self.jelly_cm.info
        if info is None:
            return None
        extra_attr: dict[str, object] = {
            "os": info["OperatingSystem"],
            "update_available": info["HasUpdateAvailable"],
            "version": info["Version"],
        }
        if self.jelly_cm.data:
            extra_attr["data"] = self.jelly_cm.data
        if self.jelly_cm.yamc:
            extra_attr["yamc"] = self.jelly_cm.yamc

        return extra_attr

    async def async_update(self) -> None:
        """Synchronise state from the server."""
        autolog("<<<")
        await self.jelly_cm.update_data()

    async def async_trigger_scan(self) -> None:
        _LOGGER.info("Library scan triggered")
        await self.jelly_cm.trigger_scan()

    async def async_delete_item(self, id: str) -> None:
        _LOGGER.debug("async_delete_item triggered")
        await self.jelly_cm.delete_item(id)
        self.async_schedule_update_ha_state()

    async def async_search_item(self, search_term: str) -> None:
        _LOGGER.debug("async_search_item triggered: %s", search_term)
        await self.jelly_cm.search_item(search_term)
        self.async_schedule_update_ha_state()

    async def async_yamc_setpage(self, page: int) -> None:
        _LOGGER.debug("YAMC setpage: %d", page)

        await self.jelly_cm.yamc_set_page(page)
        self.async_schedule_update_ha_state()

    async def async_yamc_setplaylist(self, playlist: str) -> None:
        _LOGGER.debug("YAMC setplaylist: %s", playlist)

        await self.jelly_cm.yamc_set_playlist(playlist)
        self.async_schedule_update_ha_state()

