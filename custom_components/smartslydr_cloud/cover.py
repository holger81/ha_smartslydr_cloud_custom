"""Cover platform for SmartSlydr."""
from __future__ import annotations


import time
from homeassistant.components.cover import CoverEntity, CoverDeviceClass, CoverEntityFeature, ATTR_POSITION
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from typing import Any

from .const import DOMAIN, LOGGER, NAME, DEVICE_MODEL, MAX_MOVE_SECONDS
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
        # Real (non-optimistic) position as last reported by the API
        self._last_api_pos = device.position
        # Timestamp until which a move may run before the watchdog kicks in
        self._move_deadline = 0.0

    def _start_move(self, direction: int, target: int) -> None:
        """Remember move metadata and (re)arm the stuck-move watchdog."""
        self._last_api_pos = self._roller.position
        self._move_deadline = time.monotonic() + MAX_MOVE_SECONDS
        self._roller.moving = direction
        self._target_position = target

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

        data = self.coordinator.data[self._roller.device_id]
        self._roller.error = data.error
        self._roller.temperature = data.temperature
        self._roller.humidity = data.humidity
        self._roller.wlansignal = data.wlansignal
        self._roller.status = data.status

        # While moving, follow the real API position (the cloud lags behind the
        # device and initially keeps reporting the pre-move position). Arrival
        # is only signalled by data; a watchdog below clears the moving state
        # if the API never catches up, so the entity can never get stuck in
        # "opening"/"closing".
        if self._roller.moving != 0:
            new_pos = data.position
            made_progress = self._roller.moving > 0 and new_pos > self._last_api_pos
            made_progress = made_progress or (
                self._roller.moving < 0 and new_pos < self._last_api_pos
            )
            if self._arrived_at_target(new_pos):
                self._roller.position = new_pos
                self._last_api_pos = new_pos
                self._roller.moving = 0
                self._target_position = None
            elif made_progress:
                self._roller.position = new_pos
                self._last_api_pos = new_pos
            elif time.monotonic() > self._move_deadline:
                LOGGER.warning(
                    "%s - %s still reported as moving after %s seconds; "
                    "trusting API position %s",
                    DOMAIN,
                    self._roller.devicename,
                    MAX_MOVE_SECONDS,
                    new_pos,
                )
                self._roller.position = new_pos
                self._last_api_pos = new_pos
                self._roller.moving = 0
                self._target_position = None
            # else: no usable progress in this update, keep optimistic view
        else:
            self._roller.position = data.position
            self._last_api_pos = data.position
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
        """Refresh while a move is in progress; stop once the device arrived."""
        if self._refresh_timer_handle:
            self._refresh_timer_handle.cancel()
            self._refresh_timer_handle = None
        if self._roller.moving == 0:
            return
        if time.monotonic() > self._move_deadline:
            # No update ever confirmed the move (e.g. API unreachable);
            # stop claiming motion and fall back to the last known position.
            LOGGER.warning(
                "%s - %s still reported as moving after %s seconds without "
                "API confirmation; resetting to last known position %s",
                DOMAIN,
                self._roller.devicename,
                MAX_MOVE_SECONDS,
                self._last_api_pos,
            )
            self._roller.moving = 0
            self._target_position = None
            self._roller.position = self._last_api_pos
            self.async_write_ha_state()
            return
        self._refresh_timer_handle = self.hass.loop.call_later(
            delay_seconds,
            self._refresh_and_recheck,
        )

    def _refresh_and_recheck(self) -> None:
        """Refresh from the API, then keep polling until the move has ended."""
        self._refresh_timer_handle = None
        self.hass.async_create_task(self.coordinator.async_request_refresh())
        self._schedule_refresh_after_move()

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.coordinator.client.setPosition(self._roller.device_id, 100)
        self._start_move(1, 100)
        self._roller.position = 100  # Optimistic
        self.async_write_ha_state()
        self._schedule_refresh_after_move()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self.coordinator.client.setPosition(self._roller.device_id, 0)
        self._start_move(-1, 0)
        self._roller.position = 0  # Optimistic
        self.async_write_ha_state()
        self._schedule_refresh_after_move()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set the cover to a specific position."""
        target = kwargs[ATTR_POSITION]
        await self.coordinator.client.setPosition(self._roller.device_id, target)
        if self._roller.position > target:
            direction = -1
        elif self._roller.position < target:
            direction = 1
        else:
            direction = 0
        self._start_move(direction, target)
        self._roller.position = target  # Optimistic
        self.async_write_ha_state()
        self._schedule_refresh_after_move()
