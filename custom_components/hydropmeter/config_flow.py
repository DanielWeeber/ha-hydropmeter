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
    AUTHOR_URL,
    CONF_API_KEY,
    CONF_ENABLE_FLOW_SENSOR,
    CONF_ENTITY_UNIQUE_ID,
    CONF_SCAN_INTERVAL,
    CONF_SENSOR_NAME,
    DEFAULT_ENABLE_FLOW_SENSOR,
    DEFAULT_ENTITY_UNIQUE_ID,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SENSOR_NAME,
    DOMAIN,
    INTEGRATION_URL,
)

_LOGGER = logging.getLogger(__name__)


def _current(entry: config_entries.ConfigEntry, key: str, default: Any = None) -> Any:
    """Aktuellen Wert aus options (bevorzugt) oder data lesen."""
    return entry.options.get(key, entry.data.get(key, default))


class HydropMeterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow für die Hydropmeter Integration."""

    VERSION = 1

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> HydropMeterOptionsFlow:
        """Options Flow für nachträgliche Änderungen."""
        return HydropMeterOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Einrichtungsformular anzeigen und verarbeiten."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await _validate_api(self.hass, user_input)
            if not errors:
                return self.async_create_entry(
                    title=user_input.get("name", DEFAULT_NAME),
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required("name", default=DEFAULT_NAME): str,
                vol.Required(CONF_SENSOR_NAME, default=DEFAULT_SENSOR_NAME): str,
                vol.Required(CONF_API_KEY): str,
                vol.Optional(
                    CONF_ENTITY_UNIQUE_ID, default=DEFAULT_ENTITY_UNIQUE_ID
                ): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=86400)),
                vol.Optional(
                    CONF_ENABLE_FLOW_SENSOR, default=DEFAULT_ENABLE_FLOW_SENSOR
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "author_url": AUTHOR_URL,
                "docs_url": INTEGRATION_URL,
            },
        )


class HydropMeterOptionsFlow(config_entries.OptionsFlow):
    """Options Flow – Einstellungen nach der Ersteinrichtung ändern."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialisierung."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Optionsformular anzeigen und verarbeiten."""
        errors: dict[str, str] = {}
        entry = self.config_entry

        if user_input is not None:
            errors = await _validate_api(self.hass, user_input)
            if not errors:
                # Titel aktualisieren falls Name geändert wurde
                self.hass.config_entries.async_update_entry(
                    entry,
                    title=user_input.get("name", entry.title),
                )
                return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    "name", default=_current(entry, "name", DEFAULT_NAME)
                ): str,
                vol.Required(
                    CONF_SENSOR_NAME,
                    default=_current(entry, CONF_SENSOR_NAME, DEFAULT_SENSOR_NAME),
                ): str,
                vol.Required(
                    CONF_API_KEY,
                    default=_current(entry, CONF_API_KEY, ""),
                ): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=_current(entry, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=86400)),
                vol.Optional(
                    CONF_ENABLE_FLOW_SENSOR,
                    default=_current(
                        entry, CONF_ENABLE_FLOW_SENSOR, DEFAULT_ENABLE_FLOW_SENSOR
                    ),
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )


async def _validate_api(hass: Any, data: dict[str, Any]) -> dict[str, str]:
    """API-Verbindung testen – gibt spezifische Fehlercodes zurück."""
    errors: dict[str, str] = {}
    session = async_get_clientsession(hass)
    url = f"{API_BASE_URL}/{data[CONF_SENSOR_NAME]}/newest"
    headers = {"apikey": data[CONF_API_KEY]}

    _LOGGER.debug("Hydropmeter: Verbindungstest zu %s", url)

    try:
        async with session.get(
            url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            _LOGGER.debug("Hydropmeter: API-Antwort Status=%s", response.status)

            if response.status in (401, 403):
                errors["base"] = "invalid_auth"
            elif response.status == 404:
                errors["base"] = "sensor_not_found"
            elif response.status >= 500:
                errors["base"] = "server_error"
            elif not response.ok:
                _LOGGER.warning(
                    "Hydropmeter: Unerwarteter HTTP-Status %s", response.status
                )
                errors["base"] = "cannot_connect"
            else:
                try:
                    json_data = await response.json(content_type=None)
                except Exception:
                    _LOGGER.exception("Hydropmeter: JSON-Parsing fehlgeschlagen")
                    errors["base"] = "invalid_response"
                else:
                    sensors = json_data.get("sensors")
                    if not sensors:
                        _LOGGER.warning(
                            "Hydropmeter: Keine Sensoren in Antwort: %s",
                            str(json_data)[:200],
                        )
                        errors["base"] = "no_sensor_data"
                    elif not sensors[0].get("records"):
                        _LOGGER.warning(
                            "Hydropmeter: Sensor gefunden, aber keine Messwerte"
                        )
                        errors["base"] = "no_records"

    except aiohttp.ClientConnectorError:
        _LOGGER.exception("Hydropmeter: Netzwerkverbindung fehlgeschlagen")
        errors["base"] = "network_error"
    except aiohttp.ServerTimeoutError:
        _LOGGER.warning("Hydropmeter: API-Timeout (>15s)")
        errors["base"] = "timeout"
    except aiohttp.ClientError:
        _LOGGER.exception("Hydropmeter: Verbindungsfehler")
        errors["base"] = "cannot_connect"
    except Exception:
        _LOGGER.exception("Hydropmeter: Unbekannter Fehler beim Verbindungstest")
        errors["base"] = "unknown"

    if not errors:
        _LOGGER.debug("Hydropmeter: Verbindungstest erfolgreich")

    return errors
