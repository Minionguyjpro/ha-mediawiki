from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from functools import partial

from mediawiki import (
    MediaWiki,
    MediaWikiException,
)
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv

from .const import CONF_INSTANCES, CONF_URL, LOGGER


class MediaWikiConfigFlow(ConfigFlow, domain="mediawiki"):
    VERSION = 1

    def __init__(self) -> None:
        self._client: MediaWiki | None = None

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        return await self.async_step_instances(user_input)    

    async def async_step_instances(
        self,
        user_input: dict[str, Any]  | None = None,
     ) -> ConfigFlowResult:
        if not user_input:
            return self.async_show_form(
                step_id="instances",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_URL): str,
                    }
            ),
        )

        url = user_input[CONF_URL]
        self._client = await self.hass.async_add_executor_job(lambda: MediaWiki(url=url))

        try:
            response = await self.hass.async_add_executor_job(self._client.api_version)
        except MediaWikiException as exception:
            LOGGER.exception(exception)
            return self.async_show_form(
                step_id="instances",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_URL): str
                    }
                ),
                errors={"base": "cannot_connect"}
            )

        return self.async_create_entry(
            title="",
            data={CONF_INSTANCES: [{"url": url}]},
        )
