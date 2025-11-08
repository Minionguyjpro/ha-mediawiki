from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import MediaWikiConfigEntry, MediaWikiDataUpdateCoordinator

from .const import LOGGER


@dataclass(frozen=True, kw_only=True)
class MediaWikiSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], StateType]

    attr_fn: Callable[[dict[str, Any]], Mapping[str, Any] | None] = lambda data: None
    avabl_fn: Callable[[dict[str, Any]], bool] = lambda data: True


SENSOR_DESCRIPTIONS: tuple[MediaWikiSensorEntityDescription, ...] = (
    MediaWikiSensorEntityDescription(
        key="images_count",
        translation_key="images_count",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["statistics"]["images"],
    ),
    MediaWikiSensorEntityDescription(
        key="pages_count",
        translation_key="pages_count",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["statistics"]["pages"],
    ),
    MediaWikiSensorEntityDescription(
        key="software_version",
        translation_key="software_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["general"]["generator"],
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: MediaWikiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    instances = entry.runtime_data
    async_add_entities(
        (
            MediaWikiSensorEntity(coordinator, description)
            for description in SENSOR_DESCRIPTIONS
            for coordinator in instances.values()
        ),
    )

class MediaWikiSensorEntity(CoordinatorEntity[MediaWikiDataUpdateCoordinator], SensorEntity):
    _attr_attribution = "Data provided by the MediaWiki instance's API"
    _attr_has_entity_name = True

    entity_description: MediaWikiSensorEntityDescription

    def __init__(
        self,
        coordinator: MediaWikiDataUpdateCoordinator,
        entity_description: MediaWikiSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator=coordinator)
        
        self.entity_description = entity_description

        wiki_name = (
            coordinator.data.get("general", {}).get("sitename")
            if coordinator.data else coordinator.instance["url"]
        )
        normalized_name = wiki_name.lower().replace(" ", "_")

        LOGGER.debug(
            "Initializing MediaWikiSensorEntity: wiki_name=%s, description=%s, key=%s",
            wiki_name,
            entity_description,
            entity_description.key,
        )
        
        self._attr_unique_id = f"{normalized_name}_{entity_description.key}"
    
        self._attr_device_info = DeviceInfo(
            identifiers={("mediawiki", coordinator.instance["url"])},
            name=wiki_name,
            manufacturer="MediaWiki",
            configuration_url=coordinator.instance["url"],
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.coordinator.data is not None
            and self.entity_description.avabl_fn(self.coordinator.data)
        )

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        return self.entity_description.attr_fn(self.coordinator.data)
