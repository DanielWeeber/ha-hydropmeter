"""Config Flow für die Hydropmeter Integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_BASE_URL,
    CONF_API_KEY,
    CONF_DEVICE_ID,
    CONF_ENTITY_UNIQUE_ID,
    CONF_SCAN_INTERVAL,
    CONF_SENSOR_NAME,
    DEFAULT_ENTITY_UNIQUE_ID,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SENSOR_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class HydropMeterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow für die Hydropmeter Integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ersten Einrichtungsschritt verarbeiten."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await self._validate_input(user_input)
            if not errors:
                return self.async_create_entry(
                    title=user_input.get("name", DEFAULT_NAME),
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required("name", default=DEFAULT_NAME): str,
                vol.Required(CONF_DEVICE_ID): str,
                vol.Required(CONF_SENSOR_NAME, default=DEFAULT_SENSOR_NAME): str,
                vol.Required(CONF_API_KEY): str,
                vol.Optional(
                    CONF_ENTITY_UNIQUE_ID, default=DEFAULT_ENTITY_UNIQUE_ID
                ): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=86400)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def _validate_input(self, data: dict[str, Any]) -> dict[str, str]:
        """API-Verbindung testen und Eingaben validieren."""
        errors: dict[str, str] = {}
        session = async_get_clientsession(self.hass)
        url = (
            f"{API_BASE_URL}/{data[CONF_DEVICE_ID]}"
            f"/{data[CONF_SENSOR_NAME]}/newest"
        )
        headers = {"apikey": data[CONF_API_KEY]}

        try:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 401:
                    errors["base"] = "invalid_auth"
                elif response.status == 404:
                    errors["base"] = "cannot_connect"
                elif not response.ok:
                    errors["base"] = "cannot_connect"
                else:
                    json_data = await response.json()
                    if not json_data.get("sensors"):
                        errors["base"] = "cannot_connect"

        except aiohttp.ClientError:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unbekannter Fehler bei der Verbindungsprüfung")
            errors["base"] = "unknown"

        return errors
