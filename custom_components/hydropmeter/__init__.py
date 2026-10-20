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
    CONF_ENTITY_UNIQUE_ID,
    CONF_MAX_FLOW,
    CONF_SCAN_INTERVAL,
    CONF_SENSOR_NAME,
    DEFAULT_ENABLE_FLOW_SENSOR,
    DEFAULT_ENTITY_UNIQUE_ID,
    DEFAULT_MAX_FLOW,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .meter_filter import MeterFilter

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Integration nach Optionsänderung neu laden."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Hydropmeter Integration aus einem Config Entry einrichten."""
    # entry.options hat Vorrang (gesetzt nach Options-Flow-Änderungen)
    def _conf(key: str, default=None):
        return entry.options.get(key, entry.data.get(key, default))

    api_key = _conf(CONF_API_KEY)
    sensor_name = _conf(CONF_SENSOR_NAME)
    scan_interval = _conf(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    enable_flow = _conf(CONF_ENABLE_FLOW_SENSOR, DEFAULT_ENABLE_FLOW_SENSOR)
    max_flow = float(_conf(CONF_MAX_FLOW, DEFAULT_MAX_FLOW))

    session = async_get_clientsession(hass)
    previous_data: list[dict | None] = [None]
    meter_filter = MeterFilter(max_flow_m3h=max_flow)
    _seed_filter(hass, entry, meter_filter)

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
                raw_value = record.get("meterValue")
                current_value = None
                accepted = False
                if raw_value is not None:
                    try:
                        current_value, accepted = meter_filter.process(
                            float(raw_value), time.time()
                        )
                    except (TypeError, ValueError):
                        _LOGGER.debug("Hydropmeter: Zählerstand nicht lesbar: %s", raw_value)
                    if not accepted and current_value is not None:
                        _LOGGER.warning(
                            "Hydropmeter: unplausiblen Zählerstand %s m³ verworfen "
                            "(letzter gültiger Wert %s m³, Grenze %s m³/h)",
                            raw_value,
                            current_value,
                            max_flow,
                        )

                # Durchflussrate in m³/h (nur wenn aktiviert)
                flow_m3h: float | None = None
                if enable_flow and accepted and previous_data[0] is not None:
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

                if accepted:
                    previous_data[0] = {
                        "meter_value": current_value,
                        "fetched_at": fetch_time,
                    }

                return {
                    "meter_value": current_value,
                    "raw_value": raw_value,
                    "rejected_readings": meter_filter.rejected_count,
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

    # Reload auslösen wenn Optionen über den Options-Flow geändert werden
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


def _seed_filter(hass: HomeAssistant, entry: ConfigEntry, meter_filter: MeterFilter) -> None:
    """Filter mit dem letzten bekannten Zählerstand vorbelegen (Neustart/Neuladen).

    Ohne Startwert würde ein Lesefehler direkt nach dem Start ungeprüft übernommen.
    """
    try:
        from homeassistant.helpers import entity_registry as er
        from homeassistant.helpers.restore_state import async_get as async_get_restore

        uid = entry.data.get(CONF_ENTITY_UNIQUE_ID, DEFAULT_ENTITY_UNIQUE_ID)
        entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, uid)
        if not entity_id:
            return
        state = hass.states.get(entity_id)
        if state is None:
            stored = async_get_restore(hass).last_states.get(entity_id)
            state = stored.state if stored else None
        if state is None:
            return
        meter_filter.seed(float(state.state), state.last_updated.timestamp())
        _LOGGER.debug("Hydropmeter: Startwert %s m³ übernommen", state.state)
    except (TypeError, ValueError, AttributeError, KeyError) as err:
        _LOGGER.debug("Hydropmeter: kein Startwert für den Filter (%s)", err)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Integration entladen."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
