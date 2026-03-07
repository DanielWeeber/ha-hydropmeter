"""Konstanten für die Hydropmeter Integration."""
import json
from pathlib import Path

DOMAIN = "hydropmeter"

# Version aus manifest.json lesen – nur dort pflegen
_manifest = json.loads((Path(__file__).parent / "manifest.json").read_text())
VERSION = _manifest.get("version", "unknown")

# Links
INTEGRATION_URL = "https://github.com/DanielWeeber/ha-hydropmeter"
AUTHOR_URL = "https://github.com/DanielWeeber"
AUTHOR_NAME = "Daniel Weeber"
MANUFACTURER = "Hydrop Systems"
MANUFACTURER_URL = "https://hydrop-systems.com"
INTEGRATION_AUTHOR = "DanielWeeber"

# Config-Schlüssel
CONF_SENSOR_NAME = "sensor_name"
CONF_API_KEY = "api_key"
CONF_ENTITY_UNIQUE_ID = "entity_unique_id"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_ENABLE_FLOW_SENSOR = "enable_flow_sensor"

# Standardwerte
DEFAULT_NAME = "Wasserzähler"
DEFAULT_SENSOR_NAME = "Wasserzähler"
DEFAULT_ENTITY_UNIQUE_ID = "wasserzaehler_hydrop"
DEFAULT_SCAN_INTERVAL = 300  # 5 Minuten
DEFAULT_ENABLE_FLOW_SENSOR = False

# API – "ID" ist ein fester Bestandteil der URL (kein Platzhalter)
API_BASE_URL = "https://api.hydrop-systems.com/sensors/ID"
