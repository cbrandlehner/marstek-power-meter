# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Sensor platform for the Marstek Power Meter integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ENERGY_LABELS
from .const import DOMAIN


def _power(key: str, translation_key: str) -> SensorEntityDescription:
    return SensorEntityDescription(
        key=key,
        translation_key=translation_key,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    )


def _energy(key: str, translation_key: str, *, enabled: bool) -> SensorEntityDescription:
    return SensorEntityDescription(
        key=key,
        translation_key=translation_key,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
        entity_registry_enabled_default=enabled,
    )


BASE_SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    _power("total_power", "total_power"),
    _power("A_phase_power", "a_phase_power"),
    _power("B_phase_power", "b_phase_power"),
    _power("C_phase_power", "c_phase_power"),
    SensorEntityDescription(
        key="wifi_rssi",
        translation_key="wifi_rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="meter_dev_type",
        translation_key="meter_dev_type",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="meter_mac_code",
        translation_key="meter_mac_code",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="hhm_dev_type",
        translation_key="hhm_dev_type",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="hhm_mac_code",
        translation_key="hhm_mac_code",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="info_idx",
        translation_key="info_idx",
        entity_registry_enabled_default=False,
    ),
)

ENERGY_TRANSLATION_KEYS = {
    "low_price_ele_in": "low_price_ele_in",
    "normal_price_ele_in": "normal_price_ele_in",
    "low_price_ele_out": "low_price_ele_out",
    "normal_price_ele_out": "normal_price_ele_out",
}


def sensor_descriptions(entry: ConfigEntry, data: dict | None) -> tuple[SensorEntityDescription, ...]:
    """Enable the tariff registers only when this meter sends them."""
    has_energy = bool(entry.data.get("has_energy")) or (
        isinstance(data, dict) and any(data.get(key) is not None for key in ENERGY_LABELS)
    )
    energy = tuple(
        _energy(key, ENERGY_TRANSLATION_KEYS[key], enabled=has_energy) for key in ENERGY_LABELS
    )
    return BASE_SENSOR_DESCRIPTIONS + energy


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    descriptions = sensor_descriptions(entry, coordinator.data)
    async_add_entities(
        MarstekCtSensor(coordinator, description, entry) for description in descriptions
    )


class MarstekCtSensor(CoordinatorEntity, SensorEntity):
    """Marstek Power Meter sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, description: SensorEntityDescription, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        ct_mac = str(entry.data.get("ct_mac") or "unknown").upper()
        self._attr_unique_id = f"{ct_mac}_{description.key}"
        model = "Marstek CT"
        if isinstance(coordinator.data, dict) and coordinator.data.get("meter_dev_type"):
            model = str(coordinator.data["meter_dev_type"])
        self._attr_device_info = {
            "identifiers": {(DOMAIN, ct_mac)},
            "name": f"Marstek Power Meter {ct_mac[-4:]}",
            "manufacturer": "Marstek",
            "model": model,
        }

    @property
    def available(self) -> bool:
        """Unavailable when the last poll failed."""
        return self.coordinator.last_update_success and isinstance(self.coordinator.data, dict)

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        data = self.coordinator.data or {}
        return data.get(self.entity_description.key)
