from __future__ import annotations
from datetime import timedelta
from logging import Logger, getLogger

CONF_INSTANCES = "instances"

CONF_URL = "url"

LOGGER: Logger = getLogger(__package__)

FALLBACK_UPDATE_INTERVAL = timedelta(minutes=30)