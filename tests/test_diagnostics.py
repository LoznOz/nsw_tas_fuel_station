"""Tests for NSW Fuel Check diagnostics."""

from datetime import timedelta

from homeassistant.core import HomeAssistant

from custom_components.nsw_tas_fuel_station.const import DOMAIN
from custom_components.nsw_tas_fuel_station.coordinator import NSWFuelCoordinator
from custom_components.nsw_tas_fuel_station.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import HOME_LAT, HOME_LNG, STATION_NSW_A


async def test_diagnostics_exposes_api_request_accounting(
    hass: HomeAssistant, mock_config_entry, mock_api_client
) -> None:
    """Diagnostics expose logical and physical request accounting."""
    counts = {"oauth": 1, "data": 4, "retries": 2}
    mock_api_client.http_request_counts = counts
    mock_api_client.last_token_expires_in = 43200

    coordinator = NSWFuelCoordinator(
        hass=hass,
        api=mock_api_client,
        nicknames={
            "Home": {
                "location": {"latitude": HOME_LAT, "longitude": HOME_LNG},
                "stations": [
                    {
                        "station_code": STATION_NSW_A,
                        "au_state": "NSW",
                        "fuel_types": ["U91", "E10"],
                    }
                ],
            }
        },
        scan_interval=timedelta(minutes=5),
    )
    coordinator._last_refresh_api_operations = {
        "favorite_station": 1,
        "cheapest_nearby": 1,
    }
    coordinator._api_operations_total = 12
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = coordinator

    diagnostics = await async_get_config_entry_diagnostics(
        hass, mock_config_entry
    )

    assert diagnostics == {
        "api_request_accounting": {
            "last_refresh_api_operations": {
                "favorite_station": 1,
                "cheapest_nearby": 1,
            },
            "session_api_operations_total": 12,
            "http_request_counts": {
                "oauth": 1,
                "data": 4,
                "retries": 2,
            },
            "session_http_requests_total": 5,
            "last_token_expires_in": 43200,
        }
    }


async def test_diagnostics_handles_released_client_without_http_counters(
    hass: HomeAssistant, mock_config_entry, mock_api_client
) -> None:
    """Diagnostics remain available when client HTTP counters are unsupported."""
    mock_api_client.http_request_counts = None

    coordinator = NSWFuelCoordinator(
        hass=hass,
        api=mock_api_client,
        nicknames={},
        scan_interval=timedelta(minutes=5),
    )
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = coordinator

    diagnostics = await async_get_config_entry_diagnostics(
        hass, mock_config_entry
    )

    accounting = diagnostics["api_request_accounting"]
    assert accounting["http_request_counts"] is None
    assert accounting["session_http_requests_total"] is None
