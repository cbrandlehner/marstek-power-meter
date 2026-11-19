# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Config flow for the Marstek Power Meter integration."""
from __future__ import annotations

import logging
import os

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST

from .api import discover_meter
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def new_poller_mac() -> str:
    """Locally administered unicast MAC. It must not be a real battery."""
    raw = bytearray(os.urandom(6))
    raw[0] = (raw[0] | 0x02) & 0xFE
    return raw.hex().upper()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Ask for the meter IP, then detect CT type and MAC."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = str(user_input[CONF_HOST]).strip()
            try:
                found = await self.hass.async_add_executor_job(
                    discover_meter, host, new_poller_mac()
                )
            except Exception:
                _LOGGER.exception("Unexpected error during discovery")
                errors["base"] = "unknown"
            else:
                if not isinstance(found, dict) or "error" in found:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(found["ct_mac"].upper())
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"Marstek Power Meter {host}",
                        data=found,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )
