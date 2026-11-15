# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Config flow for the Marstek Power Meter integration."""
from __future__ import annotations

import logging
import os
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import ENERGY_LABELS, MarstekCtApi, CannotConnect, canonical_mac
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CT_TYPES = ["HME-4", "TPM2-0", "HME-3"]
DEVICE_TYPE_PREFIXES = ["HMG", "HMB", "HMA", "HMK"]


def new_poller_mac() -> str:
    """Locally administered unicast MAC. It must not be a real battery."""
    raw = bytearray(os.urandom(6))
    raw[0] = (raw[0] | 0x02) & 0xFE
    return raw.hex().upper()


def _user_schema(poller_mac: str) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST): str,
            vol.Required("battery_mac", default=poller_mac): str,
            vol.Required("ct_mac"): str,
            vol.Required("device_type_prefix", default="HMG"): SelectSelector(
                SelectSelectorConfig(
                    options=DEVICE_TYPE_PREFIXES,
                    translation_key="device_type_prefix",
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required("device_type_number", default="50"): str,
            vol.Required("ct_type", default="HME-4"): SelectSelector(
                SelectSelectorConfig(
                    options=CT_TYPES,
                    translation_key="ct_type",
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input and bind the entry to the CT that answered."""
    api = MarstekCtApi(
        host=data[CONF_HOST],
        device_type=data["device_type"],
        battery_mac=data["battery_mac"],
        ct_mac=data["ct_mac"],
        ct_type=data["ct_type"],
    )

    result = await hass.async_add_executor_job(api.fetch_data)
    if isinstance(result, dict) and "error" in result:
        raise CannotConnect(result["error"])

    reported_mac = result.get("meter_mac_code") if isinstance(result, dict) else None
    if isinstance(reported_mac, str):
        try:
            data["ct_mac"] = canonical_mac(reported_mac)
        except ValueError:
            pass

    reported_type = result.get("meter_dev_type") if isinstance(result, dict) else None
    if isinstance(reported_type, str) and reported_type in CT_TYPES:
        data["ct_type"] = reported_type

    if any(result.get(key) is not None for key in ENERGY_LABELS):
        data["has_energy"] = True

    return {"title": f"Marstek Power Meter {data[CONF_HOST]}"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the integration."""

    VERSION = 1

    def __init__(self) -> None:
        self._poller_mac = new_poller_mac()

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            final_data = dict(user_input)
            final_data["device_type"] = (
                f"{final_data['device_type_prefix']}-{final_data['device_type_number']}"
            )
            final_data.pop("device_type_prefix", None)
            final_data.pop("device_type_number", None)

            try:
                final_data["battery_mac"] = canonical_mac(final_data["battery_mac"])
                final_data["ct_mac"] = canonical_mac(final_data["ct_mac"])
            except ValueError:
                errors["base"] = "invalid_mac"
            else:
                if final_data["battery_mac"].upper() == final_data["ct_mac"].upper():
                    errors["base"] = "invalid_mac"
                else:
                    try:
                        info = await validate_input(self.hass, final_data)
                    except CannotConnect:
                        errors["base"] = "cannot_connect"
                    except Exception:
                        _LOGGER.exception("Unexpected error during validation")
                        errors["base"] = "unknown"
                    else:
                        await self.async_set_unique_id(final_data["ct_mac"].upper())
                        self._abort_if_unique_id_configured()
                        return self.async_create_entry(title=info["title"], data=final_data)

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(self._poller_mac),
            errors=errors,
        )
