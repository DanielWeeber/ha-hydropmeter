"""Hydropmeter – Home Assistant Integration für den Hydrop Systems Wasserzähler.

Entwickelt von DanielWeeber (https://github.com/DanielWeeber).
Hardware: Hydrop Systems (https://hydrop-systems.com)
"""
from __future__ import annotations

import logging
import time
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE_URL,
    CONF_API_KEY,
    CONF_ENABLE_FLOW_SENSOR,
    CONF_SCAN_INTERVAL,
    CONF_SENSOR_NAME,
    DEFAULT_ENABLE_FLOW_SENSOR,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Hydropmeter Integration aus einem Config Entry einrichten."""
    api_key = entry.data[CONF_API_KEY]
    sensor_name = entry.data[CONF_SENSOR_NAME]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    enable_flow = entry.data.get(CONF_ENABLE_FLOW_SENSOR, DEFAULT_ENABLE_FLOW_SENSOR)

    session = async_get_clientsession(hass)
    previous_data: list[dict | None] = [None]

    async def async_fetch_data() -> dict:
        """Aktuelle Zählerdaten und Gerätemetadaten von der Hydrop API abrufen."""
        url = f"{API_BASE_URL}/{sensor_name}/newest"
        headers = {"apikey": api_key}
        fetch_time = time.monotonic()

        try:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)

                sensors = data.get("sensors")
                if not sensors or not sensors[0].get("records"):
                    raise UpdateFailed(
                        "Die API-Antwort enthält keine Sensordaten. "
                        "Bitte die Sensor-Bezeichnung in der Integration prüfen."
                    )

                record = sensors[0]["records"][0]
                current_value = record.get("meterValue")

                # Durchflussrate in m³/h (nur wenn aktiviert)
                flow_m3h: float | None = None
                if enable_flow and previous_data[0] is not None and current_value is not None:
                    try:
                        delta_m3 = float(current_value) - float(
                            previous_data[0]["meter_value"]
                        )
                        delta_hours = (
                            fetch_time - previous_data[0]["fetched_at"]
                        ) / 3600
                        if delta_hours > 0 and delta_m3 >= 0:
                            flow_m3h = round(delta_m3 / delta_hours, 4)
                    except (TypeError, ValueError):
                        _LOGGER.debug(
                            "Hydropmeter: Durchflussberechnung nicht möglich"
                        )

                if current_value is not None:
                    previous_data[0] = {
                        "meter_value": current_value,
                        "fetched_at": fetch_time,
                    }

                return {
                    "meter_value": current_value,
                    "timestamp": record.get("timestamp"),
                    "flow_m3h": flow_m3h,
                }

        except aiohttp.ClientResponseError as err:
            if err.status == 401:
                raise UpdateFailed("Ungültiger API-Schlüssel (401).") from err
            if err.status == 404:
                raise UpdateFailed(
                    "Sensor nicht gefunden (404). Bitte die Sensor-Bezeichnung prüfen."
                ) from err
            raise UpdateFailed(f"HTTP-Fehler {err.status}: {err.message}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Verbindungsfehler zur Hydrop API: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=async_fetch_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(
            f"Initialer Datenabruf fehlgeschlagen: {err}"
        ) from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Integration entladen."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
