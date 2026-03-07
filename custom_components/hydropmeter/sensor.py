"""Sensor-Entitäten für die Hydropmeter Integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    AUTHOR_URL,
    CONF_ENABLE_FLOW_SENSOR,
    CONF_ENTITY_UNIQUE_ID,
    CONF_SENSOR_NAME,
    DEFAULT_ENABLE_FLOW_SENSOR,
    DEFAULT_ENTITY_UNIQUE_ID,
    DEFAULT_NAME,
    DOMAIN,
    INTEGRATION_AUTHOR,
    INTEGRATION_URL,
    MANUFACTURER,
)

# Mapping bekannter API-Feldnamen → HA device_info-Schlüssel
_FIRMWARE_KEYS = ("firmwareVersion", "firmware_version", "firmware", "swVersion", "sw_version")
_SERIAL_KEYS = ("serialNumber", "serial_number", "serial", "id", "deviceId", "device_id")
_MAC_KEYS = ("macAddress", "mac_address", "mac", "macAddr")
_MODEL_KEYS = ("model", "modelName", "model_name", "deviceModel", "device_model")
_HW_KEYS = ("hardwareVersion", "hardware_version", "hwVersion", "hw_version")


def _first(d: dict, keys: tuple) -> str | None:
    """Ersten vorhandenen Wert aus einem Dict für eine Liste von Schlüsseln zurückgeben."""
    for k in keys:
        v = d.get(k)
        if v is not None:
            return str(v)
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Hydropmeter Sensoren aus einem Config Entry einrichten."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list = [HydropMeterSensor(coordinator, entry)]
    if entry.data.get(CONF_ENABLE_FLOW_SENSOR, DEFAULT_ENABLE_FLOW_SENSOR):
        entities.append(HydropFlowM3hSensor(coordinator, entry))
    async_add_entities(entities)


class _HydropBaseSensor(CoordinatorEntity, SensorEntity):
    """Gemeinsame Basis für alle Hydropmeter-Sensoren."""

    _attr_attribution = (
        f"Integration by {INTEGRATION_AUTHOR} ({AUTHOR_URL})"
        f" · Hardware by {MANUFACTURER}"
    )

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> dict:
        """Geräteinformationen – wird in die HA Device Registry geschrieben."""
        meta: dict = {}
        if self.coordinator.data:
            meta = self.coordinator.data.get("device_meta", {})

        sensor_name = self._entry.data.get(CONF_SENSOR_NAME, "")

        info: dict = {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.data.get("name", DEFAULT_NAME),
            "manufacturer": MANUFACTURER,
            "model": _first(meta, _MODEL_KEYS) or "Hydropmeter",
            "configuration_url": INTEGRATION_URL,
        }

        # Sensor-Name als Modellzusatz wenn kein Modell aus API
        if not _first(meta, _MODEL_KEYS) and sensor_name:
            info["model"] = f"Hydropmeter ({sensor_name})"

        # Optionale Felder aus der API-Antwort
        if fw := _first(meta, _FIRMWARE_KEYS):
            info["sw_version"] = fw

        if hw := _first(meta, _HW_KEYS):
            info["hw_version"] = hw

        if serial := _first(meta, _SERIAL_KEYS):
            info["serial_number"] = serial

        if mac := _first(meta, _MAC_KEYS):
            info["connections"] = {("mac", mac.upper())}

        return info


class HydropMeterSensor(_HydropBaseSensor):
    """Gesamtzählerstand in m³ (total_increasing, kompatibel mit Energie-Dashboard)."""

    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "m³"
    _attr_icon = "mdi:water-pump"

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = entry.data.get("name", DEFAULT_NAME)
        self._attr_unique_id = entry.data.get(
            CONF_ENTITY_UNIQUE_ID, DEFAULT_ENTITY_UNIQUE_ID
        )

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            raw = self.coordinator.data.get("meter_value")
            try:
                return float(raw) if raw is not None else None
            except (ValueError, TypeError):
                return None
        return None

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        attrs: dict = {
            "timestamp": self.coordinator.data.get("timestamp"),
            "sensor_name": self._entry.data.get(CONF_SENSOR_NAME),
        }
        # Alle unbekannten API-Felder als Attribute durchreichen
        meta = self.coordinator.data.get("device_meta", {})
        known_device_keys = set(_FIRMWARE_KEYS + _SERIAL_KEYS + _MAC_KEYS + _MODEL_KEYS + _HW_KEYS)
        for k, v in meta.items():
            if k not in known_device_keys and v is not None:
                attrs[k] = v
        return attrs


class HydropFlowM3hSensor(_HydropBaseSensor):
    """Durchflussrate in m³/h, berechnet aus aufeinanderfolgenden Zählerständen."""

    _attr_device_class = SensorDeviceClass.VOLUME_FLOW_RATE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "m³/h"
    _attr_icon = "mdi:waves-arrow-right"

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        sensor_name = entry.data.get(CONF_SENSOR_NAME, DEFAULT_NAME)
        uid = entry.data.get(CONF_ENTITY_UNIQUE_ID, DEFAULT_ENTITY_UNIQUE_ID)
        self._attr_name = f"{sensor_name} Durchfluss"
        self._attr_unique_id = f"{uid}_flow_m3h"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("flow_m3h")
        return None
