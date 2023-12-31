"""SmartSlydrEntity class."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, NAME, VERSION
from .coordinator import SmartSlydrCloudUpdateCoordinator


class SmartSlydrEntity(CoordinatorEntity):
    """SmartSlydrEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: SmartSlydrCloudUpdateCoordinator, device_id: str) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{device_id}_cover"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=NAME,
            model=VERSION,
            manufacturer=NAME,
        )
