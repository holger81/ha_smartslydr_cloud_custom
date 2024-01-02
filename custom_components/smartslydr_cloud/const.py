"""Constants for smartslydr_cloud."""
from logging import Logger, getLogger

DOMAIN = "smartslydr_cloud"

NAME = "Lycheethings Cloud Custom"
VERSION = "0.0.1"
MANUFACTURER = "Lycheethings"
ATTRIBUTION = "Custom Integration for LycheeThings SmartSlydr Devices"

BASE_API_URL = "https://34yl6ald82.execute-api.us-east-2.amazonaws.com/prod/"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"

CONF_SYNC_INTERVAL = "sync_interval"

DEFAULT_SYNC_INTERVAL = 60  # seconds

LOGGER: Logger = getLogger(__package__)
