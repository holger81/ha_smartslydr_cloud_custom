"""Custom integration to integrate SmartSlydr devices from LycheeThings with Home Assistant.

For more details about this integration, please refer to
https://github.com/holger81/ha_smartslydr_cloud_custom
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import ConfigEntryNotReady

from .api import LycheeThingsApiClient
from .const import DOMAIN, CONF_SYNC_INTERVAL, DEFAULT_SYNC_INTERVAL
from .coordinator import SmartSlydrCloudUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.COVER,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    sync_interval = entry.options.get(CONF_SYNC_INTERVAL, DEFAULT_SYNC_INTERVAL)

    client = LycheeThingsApiClient(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            session=async_get_clientsession(hass),
        )

    await client.getSecurityTokens()

    hass.data[DOMAIN][entry.entry_id] = coordinator = SmartSlydrCloudUpdateCoordinator(
        hass=hass,
        client= client,
        update_interval= sync_interval,
    )
    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
