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
    CONF_ENTITY_UNIQUE_ID,
    CONF_SENSOR_NAME,
    DEFAULT_ENTITY_UNIQUE_ID,
    DEFAULT_NAME,
    DOMAIN,
    INTEGRATION_AUTHOR,
    INTEGRATION_URL,
    MANUFACTURER,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Hydropmeter Sensoren aus einem Config Entry einrichten."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            HydropMeterSensor(coordinator, entry),
            HydropFlowM3hSensor(coordinator, entry),
            HydropFlowLminSensor(coordinator, entry),
        ]
    )


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
        """Sensor initialisieren."""
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> dict:
        """Geräteinformationen für die HA-Geräteverwaltung."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.data.get("name", DEFAULT_NAME),
            "manufacturer": MANUFACTURER,
            "model": "Hydropmeter",
            "entry_type": "service",
            "configuration_url": INTEGRATION_URL,
        }


class HydropMeterSensor(_HydropBaseSensor):
    """Repräsentiert den Hydropmeter Wasserzähler als Home Assistant Sensor."""

    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "m³"
    _attr_icon = "mdi:water-pump"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Sensor initialisieren."""
        super().__init__(coordinator, entry)
        self._attr_name = entry.data.get("name", DEFAULT_NAME)
        self._attr_unique_id = entry.data.get(
            CONF_ENTITY_UNIQUE_ID, DEFAULT_ENTITY_UNIQUE_ID
        )

    @property
    def native_value(self) -> float | None:
        """Aktuellen Zählerstand zurückgeben."""
        if self.coordinator.data:
            raw = self.coordinator.data.get("meter_value")
            try:
                return float(raw) if raw is not None else None
            except (ValueError, TypeError):
                return None
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Zusätzliche Attribute zurückgeben."""
        if not self.coordinator.data:
            return {}
        return {
            "timestamp": self.coordinator.data.get("timestamp"),
            "sensor_name": self._entry.data.get(CONF_SENSOR_NAME),
        }


class HydropFlowM3hSensor(_HydropBaseSensor):
    """Durchflussrate in m³/h, abgeleitet aus aufeinanderfolgenden Zählerständen."""

    _attr_device_class = SensorDeviceClass.VOLUME_FLOW_RATE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "m³/h"
    _attr_icon = "mdi:waves-arrow-right"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Sensor initialisieren."""
        super().__init__(coordinator, entry)
        sensor_name = entry.data.get(CONF_SENSOR_NAME, DEFAULT_NAME)
        uid = entry.data.get(CONF_ENTITY_UNIQUE_ID, DEFAULT_ENTITY_UNIQUE_ID)
        self._attr_name = f"{sensor_name} Durchfluss"
        self._attr_unique_id = f"{uid}_flow_m3h"

    @property
    def native_value(self) -> float | None:
        """Aktuelle Durchflussrate in m³/h zurückgeben."""
        if self.coordinator.data:
            return self.coordinator.data.get("flow_m3h")
        return None


class HydropFlowLminSensor(_HydropBaseSensor):
    """Durchflussrate in L/min, abgeleitet aus aufeinanderfolgenden Zählerständen."""

    _attr_device_class = SensorDeviceClass.VOLUME_FLOW_RATE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "L/min"
    _attr_icon = "mdi:waves-arrow-right"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Sensor initialisieren."""
        super().__init__(coordinator, entry)
        sensor_name = entry.data.get(CONF_SENSOR_NAME, DEFAULT_NAME)
        uid = entry.data.get(CONF_ENTITY_UNIQUE_ID, DEFAULT_ENTITY_UNIQUE_ID)
        self._attr_name = f"{sensor_name} Durchfluss L/min"
        self._attr_unique_id = f"{uid}_flow_lmin"

    @property
    def native_value(self) -> float | None:
        """Aktuelle Durchflussrate in L/min zurückgeben."""
        if self.coordinator.data:
            return self.coordinator.data.get("flow_lmin")
        return None
