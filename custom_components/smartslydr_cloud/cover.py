"""Cover platform for SmartSlydr."""
from __future__ import annotations


from homeassistant.components.cover import CoverEntity, CoverDeviceClass, CoverEntityFeature, ATTR_POSITION
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from typing import Any

from .const import DOMAIN, LOGGER, NAME, DEVICE_MODEL
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
        self._target_position: int | None = None  # target when moving; used to ignore stale API data
        self._refresh_timer_handle = None  # cancel delayed refresh on new action

        # Use window/cover name as device headline in HA (e.g. "Jonathans Room")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._roller.devicename,
            model=DEVICE_MODEL,
            manufacturer=NAME,
        )
        self._attr_name = self._roller.devicename

    def _arrived_at_target(self, new_pos: int) -> bool:
        """Return whether the API position matches the commanded target (handles partial moves)."""
        if self._target_position is None:
            return True
        t = self._target_position
        if self._roller.moving > 0:  # opening toward t
            if t >= 99:
                return new_pos >= 95
            return new_pos >= t
        # closing toward t
        if t <= 1:
            return new_pos <= 5
        # partial close: near target, or device reports fully closed
        return abs(new_pos - t) <= 5 or new_pos == 0

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        LOGGER.debug(
            f"{DOMAIN} - should update!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"  # noqa: G003
            + str(self.coordinator.data)
        )

        old_position = self._roller.position
        data = self.coordinator.data[self._roller.device_id]
        self._roller.error = data.error
        self._roller.temperature = data.temperature
        self._roller.humidity = data.humidity
        self._roller.wlansignal = data.wlansignal
        self._roller.status = data.status

        # While moving, ignore stale API position (e.g. still 0 right after Open).
        # Accept real progress; complete only when truly at target (partial ≠ full close).
        if self._roller.moving != 0 and self._target_position is not None:
            new_pos = data.position
            t = self._target_position
            if self._roller.moving > 0:  # opening toward t
                stale_open = new_pos == 0 and old_position > 0 and t > 0
                if stale_open:
                    pass
                elif new_pos >= t:
                    self._roller.position = new_pos
                    self._roller.moving = 0
                    self._target_position = None
                elif new_pos > old_position:
                    self._roller.position = new_pos
                    if self._arrived_at_target(new_pos):
                        self._roller.moving = 0
                        self._target_position = None
                elif (
                    old_position >= t
                    and 0 < new_pos < old_position
                    and new_pos <= t
                ):
                    # API refines below optimistic target (e.g. 15 vs optimistic 20)
                    self._roller.position = new_pos
                    if self._arrived_at_target(new_pos):
                        self._roller.moving = 0
                        self._target_position = None
            else:  # closing toward t
                stale_close = new_pos >= 99 and old_position < 99 and t < 99
                if stale_close:
                    pass
                elif self._arrived_at_target(new_pos):
                    # e.g. optimistic position already 0 and API confirms closed
                    self._roller.position = new_pos
                    self._roller.moving = 0
                    self._target_position = None
                elif new_pos < old_position:
                    self._roller.position = new_pos
                    if self._arrived_at_target(new_pos):
                        self._roller.moving = 0
                        self._target_position = None
        else:
            self._roller.position = data.position
            self._roller.moving = 0
        self.async_write_ha_state()

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
    def is_open(self) -> bool:
        """Return True for any position above 0 (partially open counts as open).

        Home Assistant's default is often only fully open (100%); for windows we
        treat any non-zero position as open.
        """
        return self._roller.position > 0

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

    async def async_will_remove_from_hass(self) -> None:
        """Cancel pending refresh when entity is removed."""
        if self._refresh_timer_handle:
            self._refresh_timer_handle.cancel()
            self._refresh_timer_handle = None

    def _schedule_refresh_after_move(self, delay_seconds: float = 10.0) -> None:
        """Refresh from API once the move has had time to finish."""
        if self._refresh_timer_handle:
            self._refresh_timer_handle.cancel()
        self._refresh_timer_handle = self.hass.loop.call_later(
            delay_seconds,
            lambda: self.hass.async_create_task(
                self.coordinator.async_request_refresh()
            ),
        )

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.coordinator.client.setPosition(self._roller.device_id, 100)
        self._roller.moving = 1
        self._target_position = 100
        self._roller.position = 100  # Optimistic
        self.async_write_ha_state()
        self._schedule_refresh_after_move()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self.coordinator.client.setPosition(self._roller.device_id, 0)
        self._roller.moving = -1
        self._target_position = 0
        self._roller.position = 0  # Optimistic
        self.async_write_ha_state()
        self._schedule_refresh_after_move()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set the cover to a specific position."""
        target = kwargs[ATTR_POSITION]
        await self.coordinator.client.setPosition(self._roller.device_id, target)
        self._target_position = target
        if self._roller.position > target:
            self._roller.moving = -1
        elif self._roller.position < target:
            self._roller.moving = 1
        else:
            self._roller.moving = 0
        self._roller.position = target  # Optimistic
        self.async_write_ha_state()
        self._schedule_refresh_after_move()
