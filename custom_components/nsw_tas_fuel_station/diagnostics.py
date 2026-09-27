"""Diagnostics support for NSW Fuel Check."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .data import NSWFuelConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: NSWFuelConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry without exposing credentials."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    api = coordinator.api

    http_counts = getattr(api, "http_request_counts", None)
    if not isinstance(http_counts, dict):
        http_counts = None

    return {
        "api_request_accounting": {
            "last_refresh_api_operations": coordinator.last_refresh_api_operations,
            "session_api_operations_total": coordinator.api_operations_total,
            "http_request_counts": dict(http_counts) if http_counts is not None else None,
            "session_http_requests_total": (
                http_counts.get("oauth", 0) + http_counts.get("data", 0)
                if http_counts is not None
                else None
            ),
            "last_token_expires_in": getattr(api, "last_token_expires_in", None),
        }
    }
