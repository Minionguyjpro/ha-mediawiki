from __future__ import annotations

from mediawiki import MediaWiki

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from .const import CONF_INSTANCES, LOGGER
from .coordinator import MediaWikiConfigEntry, MediaWikiDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: MediaWikiConfigEntry) -> bool:
    instances: list[dict[str, str]] = entry.data[CONF_INSTANCES]

    entry.runtime_data = {}
    for instance in instances:
        coordinator = MediaWikiDataUpdateCoordinator(
            hass=hass,
            config_entry=entry,
            url=instance["url"],
        )

        await coordinator.async_config_entry_first_refresh()

        if not entry.pref_disable_polling:
            await coordinator.subscribe()

        entry.runtime_data[instance] = coordinator
    
    async_cleanup_device_registry(hass=hass, entry=entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


@callback
def async_cleanup_device_registry(
    hass: HomeAssistant,
    entry: MediaWikiConfigEntry,
) -> None:
    device_registry = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(
        registry=device_registry,
        config_entry_id=entry.entry_id,
    )
    for device in devices:
        for item in device.identifiers:
            if item[1] not in entry.options[CONF_INSTANCES]:
                LOGGER.debug(
                    (
                        "Unlinking device %s for untracked instance %s from config"
                        " entry %s"
                    ),
                    device.id,
                    item[1],
                    entry.entry_id,
                )
                device_registry.async_update_device(
                    device.id, remove_config_entry_id=entry.entry_id
                )
                break


async def async_unload_entry(hass: HomeAssistant, entry: MediaWikiConfigEntry) -> bool:
    instances = entry.runtime_data
    for coordinator in instances.values():
        coordinator.unsubscribe()

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
