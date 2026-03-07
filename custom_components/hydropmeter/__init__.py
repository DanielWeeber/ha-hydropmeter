"""Hydropmeter – Home Assistant Integration für den Hydrop Systems Wasserzähler."""
from __future__ import annotations

import logging
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
    CONF_DEVICE_ID,
    CONF_SCAN_INTERVAL,
    CONF_SENSOR_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Hydropmeter Integration aus einem Config Entry einrichten."""
    api_key = entry.data[CONF_API_KEY]
    device_id = entry.data[CONF_DEVICE_ID]
    sensor_name = entry.data[CONF_SENSOR_NAME]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    session = async_get_clientsession(hass)

    async def async_fetch_data() -> dict:
        """Aktuelle Zählerdaten von der Hydrop API abrufen."""
        url = f"{API_BASE_URL}/{device_id}/{sensor_name}/newest"
        headers = {"apikey": api_key}
        try:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                response.raise_for_status()
                data = await response.json()

                sensors = data.get("sensors")
                if not sensors or not sensors[0].get("records"):
                    raise UpdateFailed(
                        "Die API-Antwort enthält keine Sensordaten. "
                        "Bitte Geräte-ID und Sensor-Name prüfen."
                    )

                record = sensors[0]["records"][0]
                return {
                    "meter_value": record.get("meterValue"),
                    "timestamp": record.get("timestamp"),
                }

        except aiohttp.ClientResponseError as err:
            if err.status == 401:
                raise UpdateFailed("Ungültiger API-Schlüssel (401 Unauthorized).") from err
            if err.status == 404:
                raise UpdateFailed(
                    "Sensor nicht gefunden (404). Bitte Geräte-ID und Sensor-Name prüfen."
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
