"""Konstanten für die Hydropmeter Integration."""

DOMAIN = "hydropmeter"

# Config-Schlüssel
CONF_DEVICE_ID = "device_id"
CONF_SENSOR_NAME = "sensor_name"
CONF_API_KEY = "api_key"
CONF_ENTITY_UNIQUE_ID = "entity_unique_id"
CONF_SCAN_INTERVAL = "scan_interval"

# Standardwerte
DEFAULT_NAME = "Wasserzähler"
DEFAULT_SENSOR_NAME = "Wasserzähler"
DEFAULT_ENTITY_UNIQUE_ID = "wasserzaehler_hydrop"
DEFAULT_SCAN_INTERVAL = 300  # 5 Minuten

# API
API_BASE_URL = "https://api.hydrop-systems.com/sensors"
