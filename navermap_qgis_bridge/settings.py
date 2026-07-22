import json
import os
from pathlib import Path

from qgis.core import QgsSettings


PLUGIN_DIR = Path(__file__).resolve().parent
ENV_NAVER_JS_KEY = "NAVER_MAP_CLIENT_ID"
ENV_NAVER_REST_KEY = "NAVER_MAP_CLIENT_SECRET"
ENV_NAVER_API_HUB_CLIENT_ID = "NAVER_API_HUB_CLIENT_ID"
ENV_NAVER_API_HUB_CLIENT_SECRET = "NAVER_API_HUB_CLIENT_SECRET"
ENV_NAVER_MAP_BASE_URL = "NAVER_MAP_BASE_URL"
DEFAULT_NAVER_MAP_BASE_URL = "http://localhost:8082/navermap_qgis_bridge/"
SETTINGS_FILE = PLUGIN_DIR / "settings.json"
QGIS_NAVER_JS_KEY = "navermap_qgis_bridge/naver_client_id"
QGIS_NAVER_REST_KEY = "navermap_qgis_bridge/naver_client_secret"
QGIS_NAVER_API_HUB_CLIENT_ID = "navermap_qgis_bridge/naver_api_hub_client_id"
QGIS_NAVER_API_HUB_CLIENT_SECRET = (
    "navermap_qgis_bridge/naver_api_hub_client_secret"
)


def naver_map_base_url():
    value = os.getenv(ENV_NAVER_MAP_BASE_URL, "").strip()
    if not value:
        return DEFAULT_NAVER_MAP_BASE_URL
    return value.rstrip("/") + "/"


def environment_javascript_key():
    return os.getenv(ENV_NAVER_JS_KEY, "").strip()


def stored_javascript_key():
    value = QgsSettings().value(QGIS_NAVER_JS_KEY, "")
    return str(value or "").strip()


def save_javascript_key(value):
    settings = QgsSettings()
    settings.setValue(QGIS_NAVER_JS_KEY, str(value).strip())
    settings.sync()


def environment_rest_api_key():
    return os.getenv(ENV_NAVER_REST_KEY, "").strip()


def stored_rest_api_key():
    value = QgsSettings().value(QGIS_NAVER_REST_KEY, "")
    return str(value or "").strip()


def save_rest_api_key(value):
    settings = QgsSettings()
    settings.setValue(QGIS_NAVER_REST_KEY, str(value).strip())
    settings.sync()


def naver_rest_api_key():
    return environment_rest_api_key() or stored_rest_api_key()


def naver_client_id():
    return naver_javascript_key()


def naver_client_secret():
    return naver_rest_api_key()


def environment_api_hub_client_id():
    return os.getenv(ENV_NAVER_API_HUB_CLIENT_ID, "").strip()


def stored_api_hub_client_id():
    value = QgsSettings().value(QGIS_NAVER_API_HUB_CLIENT_ID, "")
    return str(value or "").strip()


def save_api_hub_client_id(value):
    settings = QgsSettings()
    settings.setValue(QGIS_NAVER_API_HUB_CLIENT_ID, str(value).strip())
    settings.sync()


def naver_api_hub_client_id():
    return environment_api_hub_client_id() or stored_api_hub_client_id()


def environment_api_hub_client_secret():
    return os.getenv(ENV_NAVER_API_HUB_CLIENT_SECRET, "").strip()


def stored_api_hub_client_secret():
    value = QgsSettings().value(QGIS_NAVER_API_HUB_CLIENT_SECRET, "")
    return str(value or "").strip()


def save_api_hub_client_secret(value):
    settings = QgsSettings()
    settings.setValue(QGIS_NAVER_API_HUB_CLIENT_SECRET, str(value).strip())
    settings.sync()


def naver_api_hub_client_secret():
    return environment_api_hub_client_secret() or stored_api_hub_client_secret()


def legacy_file_javascript_key():
    if not SETTINGS_FILE.exists():
        return ""

    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as handle:
            settings = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return ""

    return str(
        settings.get("naver_client_id", "")
        or settings.get("naver_javascript_key", "")
    ).strip()


def naver_javascript_key_source():
    if environment_javascript_key():
        return "environment"
    if stored_javascript_key():
        return "qgis"
    if legacy_file_javascript_key():
        return "file"
    return "missing"


def naver_javascript_key():
    env_value = environment_javascript_key()
    if env_value:
        return env_value

    stored_value = stored_javascript_key()
    if stored_value:
        return stored_value

    return legacy_file_javascript_key()

