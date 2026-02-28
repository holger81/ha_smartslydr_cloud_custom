"""Cover platform for SmartSlydr."""
from __future__ import annotations


from homeassistant.components.cover import CoverEntity, CoverDeviceClass, CoverEntityFeature, ATTR_POSITION
from homeassistant.core import callback
from typing import Any

from .const import DOMAIN, LOGGER
from .coordinator import SmartSlydrCloudUpdateCoordinator
from .entity import SmartSlydrEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    LOGGER.debug(f"{DOMAIN} - {coordinator.data}")  # noqa: G004
    async_add_devices(
        SmartSlydrCover(
            hass=hass,
            coordinator=coordinator,
            entry=entry,
            device=coordinator.data[device],
        )
        for device in coordinator.data
    )


class SmartSlydrCover(SmartSlydrEntity, CoverEntity):  # noqa: D101
    _attr_device_class = CoverDeviceClass.WINDOW
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(
        self,
        hass,
        coordinator: SmartSlydrCloudUpdateCoordinator,
        entry,
        device,
    ) -> None:
        """Initialize the cover."""

        super().__init__(coordinator, device.device_id)
        self.entry = entry
        self._roller = device
        # Create "moving" information
        self._roller.moving = 0
        self.hass = hass


        self._attr_name = self._roller.devicename

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        LOGGER.debug(
            f"{DOMAIN} - should update!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"  # noqa: G003
            + str(self.coordinator.data)
        )

        # Update from coordinator; position only changes when movement has stopped
        # and the API returns new data
        self._roller.error = self.coordinator.data[self._roller.device_id].error
        self._roller.position = self.coordinator.data[self._roller.device_id].position
        self._roller.temperature = self.coordinator.data[
            self._roller.device_id
        ].temperature
        self._roller.humidity = self.coordinator.data[self._roller.device_id].humidity
        self._roller.wlansignal = self.coordinator.data[
            self._roller.device_id
        ].wlansignal
        self._roller.status = self.coordinator.data[self._roller.device_id].status
        self._roller.moving = 0

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will reflect this.
    @property
    def available(self) -> bool:
        """Return True if device is available."""
        return self._roller.status == "device is online"

    # The following properties are how HA knows the current state of the device.
    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        return self._roller.position

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed, same as position 0."""
        return self._roller.position == 0

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing or not."""
        return self._roller.moving < 0

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening or not."""
        return self._roller.moving > 0

    @property
    def should_poll(self) -> bool:  # noqa: D102
        return False

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.coordinator.client.setPosition(self._roller.device_id, 100)
        self._roller.moving = 1
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self.coordinator.client.setPosition(self._roller.device_id, 0)
        self._roller.moving = -1
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set the cover to a specific position."""
        await self.coordinator.client.setPosition(
            self._roller.device_id,
            kwargs[ATTR_POSITION],
        )
        if self._roller.position > kwargs[ATTR_POSITION]:
            self._roller.moving = -1
        elif self._roller.position < kwargs[ATTR_POSITION]:
            self._roller.moving = 1
        else:
            self._roller.moving = 0
        await self.coordinator.async_request_refresh()
