"""Tests for coordinator API request accounting diagnostics."""

from datetime import timedelta

import pytest
from homeassistant.core import HomeAssistant

from custom_components.nsw_tas_fuel_station.coordinator import NSWFuelCoordinator

from .conftest import HOME_LAT, HOME_LNG, STATION_NSW_A


@pytest.fixture
def accounting_coordinator(hass: HomeAssistant, mock_api_client) -> NSWFuelCoordinator:
    """Return a coordinator with one favourite station and one cheapest query."""
    nicknames = {
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
    }
    return NSWFuelCoordinator(
        hass=hass,
        api=mock_api_client,
        nicknames=nicknames,
        scan_interval=timedelta(minutes=5),
    )


async def test_refresh_counts_logical_api_operations(
    accounting_coordinator: NSWFuelCoordinator,
) -> None:
    """A refresh counts favourite and cheapest logical API operations."""
    await accounting_coordinator._async_update_data()

    assert accounting_coordinator.last_refresh_api_operations == {
        "favorite_station": 1,
        "cheapest_nearby": 1,
    }
    assert accounting_coordinator.api_operations_total == 2


async def test_refresh_logs_http_request_delta_when_supported(
    accounting_coordinator: NSWFuelCoordinator, mock_api_client, caplog
) -> None:
    """A refresh logs HTTP deltas when the client exposes request counters."""
    counts = {"oauth": 1, "data": 4, "retries": 0}
    mock_api_client.http_request_counts = counts
    mock_api_client.last_token_expires_in = 43200

    favorite = mock_api_client.get_fuel_prices_for_station.side_effect
    cheapest = mock_api_client.get_fuel_prices_within_radius.side_effect

    async def favorite_with_count(*args, **kwargs):
        counts["data"] += 1
        return await favorite(*args, **kwargs)

    async def cheapest_with_count(*args, **kwargs):
        counts["data"] += 2
        counts["retries"] += 1
        return await cheapest(*args, **kwargs)

    mock_api_client.get_fuel_prices_for_station.side_effect = favorite_with_count
    mock_api_client.get_fuel_prices_within_radius.side_effect = cheapest_with_count

    with caplog.at_level("DEBUG"):
        await accounting_coordinator._async_update_data()

    assert "http_requests oauth=0 data=3 retries=1 total=3" in caplog.text
    assert "session_http_total=8" in caplog.text
    assert "token_expires_in=43200" in caplog.text


async def test_refresh_works_without_client_http_accounting(
    accounting_coordinator: NSWFuelCoordinator, mock_api_client, caplog
) -> None:
    """Released clients without HTTP counters retain logical-operation logging."""
    mock_api_client.http_request_counts = None

    with caplog.at_level("DEBUG"):
        await accounting_coordinator._async_update_data()

    assert "total_api_operations=2 session_total=2" in caplog.text
    assert "http_requests oauth=" not in caplog.text
