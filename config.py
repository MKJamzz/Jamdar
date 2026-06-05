import json
import os

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), ".jamdar_config.json")

_DEFAULTS = {
    "output_dir": os.path.expanduser("~/Music"),
    "default_format": "mp3",
    "spotify_client_id": "",
    "spotify_client_secret": "",
    "max_concurrent_downloads": 3,
}

_data: dict = {}


def _load():
    global _data
    if os.path.exists(_CONFIG_PATH):
        with open(_CONFIG_PATH, "r") as f:
            _data = json.load(f)
    else:
        _data = dict(_DEFAULTS)


def _save():
    with open(_CONFIG_PATH, "w") as f:
        json.dump(_data, f, indent=2)


def get(key: str):
    if not _data:
        _load()
    return _data.get(key, _DEFAULTS.get(key))


def set(key: str, value):
    if not _data:
        _load()
    _data[key] = value
    _save()


_load()
