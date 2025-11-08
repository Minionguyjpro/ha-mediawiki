from __future__ import annotations
from typing import Any

from mediawiki import (
    MediaWiki,
    MediaWikiException,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_INSTANCES, FALLBACK_UPDATE_INTERVAL, LOGGER

type MediaWikiConfigEntry = ConfigEntry[dict[str, MediaWikiDataUpdateCoordinator]]

class MediaWikiDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    config_entry: MediaWikiConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: MediaWikiConfigEntry,
        instance: dict[str, Any],
    ) -> None:
        self.instance = instance
        self._client = None
        self._init_task = hass.async_add_executor_job(MediaWiki, instance["url"])
        self.data = {}

        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=instance["url"],
            update_interval=FALLBACK_UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> MediaWiki[dict[str, Any]]:
        if self._client is None:
            self._client = await self._init_task
        
        params = {
            "action": "query",
            "meta": "siteinfo",
            "siprop": "statistics|general",
            "format": "json",
        }
        try:
            response = await self.hass.async_add_executor_job(
                self._client.wiki_request,
                params
            )
        except MediaWikiException as exception:
            LOGGER.exception(exception)
            raise UpdateFailed(exception) from exception

        query = response.get("query", {})
        statistics = query.get("statistics", {})
        general = query.get("general", {})

        self.instance["name"] = general.get("sitename", self.instance["url"])

        return {
            "statistics": statistics,
            "general": general,
        }
