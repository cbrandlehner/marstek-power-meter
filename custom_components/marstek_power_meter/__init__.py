# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The Marstek Power Meter integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MarstekCtApi, canonical_mac
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]
UPDATE_INTERVAL = timedelta(seconds=5)


def _canonicalize_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Store MACs as 12 hex digits so later polls match what the CT accepts."""
    updates: dict[str, str] = {}
    for key in ("ct_mac", "battery_mac"):
        raw = entry.data.get(key)
        if not isinstance(raw, str):
            continue
        try:
            canon = canonical_mac(raw)
        except ValueError:
            continue
        if canon != raw:
            updates[key] = canon
    if updates:
        hass.config_entries.async_update_entry(entry, data={**entry.data, **updates})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Marstek Power Meter from a config entry."""
    _canonicalize_entry(hass, entry)
    api = MarstekCtApi(
        host=entry.data["host"],
        device_type=entry.data["device_type"],
        battery_mac=entry.data["battery_mac"],
        ct_mac=entry.data["ct_mac"],
        ct_type=entry.data["ct_type"],
    )

    async def async_update_data():
        """Fetch one sample. The await covers the whole retry loop."""
        data = await hass.async_add_executor_job(api.fetch_data)
        if not isinstance(data, dict) or "error" in data:
            message = data.get("error") if isinstance(data, dict) else "No data"
            raise UpdateFailed(message)
        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="marstek_power_meter",
        update_method=async_update_data,
        update_interval=UPDATE_INTERVAL,
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
