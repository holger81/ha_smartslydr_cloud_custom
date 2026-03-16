"""Constants for smartslydr_cloud."""
from __future__ import annotations

import json
from pathlib import Path
from logging import Logger, getLogger

DOMAIN = "smartslydr_cloud"

NAME = "Lycheethings Cloud Custom"
MANUFACTURER = "Lycheethings"

# Load integration version from manifest (reflects currently installed version)
_manifest_path = Path(__file__).resolve().parent / "manifest.json"
if _manifest_path.exists():
    try:
        INTEGRATION_VERSION = json.loads(_manifest_path.read_text()).get(
            "version", "0.0.1"
        )
    except (OSError, json.JSONDecodeError):
        INTEGRATION_VERSION = "0.0.1"
else:
    INTEGRATION_VERSION = "0.0.1"

# Device model shown in HA: "SmartSlydr Custom (v0.0.9)" (strip leading v from manifest)
_version = INTEGRATION_VERSION.lstrip("v")
DEVICE_MODEL = f"SmartSlydr Custom (v{_version})"
ATTRIBUTION = "Custom Integration for LycheeThings SmartSlydr Devices"

BASE_API_URL = "https://34yl6ald82.execute-api.us-east-2.amazonaws.com/prod/"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"

CONF_SYNC_INTERVAL = "sync_interval"

DEFAULT_SYNC_INTERVAL = 60  # seconds

LOGGER: Logger = getLogger(__package__)
