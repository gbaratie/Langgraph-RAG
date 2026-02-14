"""
Service de gestion des paramètres (chunks, Docling).
Stockage dans data/settings.json.
"""
import json
from pathlib import Path
from typing import Any

# Chemin relatif au dossier api/
_SETTINGS_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_SETTINGS_FILE = _SETTINGS_DIR / "settings.json"

_DEFAULT_SETTINGS = {
    "chunks": {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "separators": ["\n\n", "\n", " ", ""],
    },
    "docling": {
        "max_num_pages": None,
        "max_file_size": None,
        "do_table_structure": True,
        "do_cell_matching": True,
        "table_former_mode": "ACCURATE",
        "enable_remote_services": False,
        "artifacts_path": None,
    },
}


def _ensure_dir() -> None:
    _SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


def get_settings() -> dict[str, Any]:
    """Charge les paramètres depuis le fichier, ou retourne les valeurs par défaut."""
    if not _SETTINGS_FILE.exists():
        return _deep_copy(_DEFAULT_SETTINGS)
    try:
        with open(_SETTINGS_FILE, encoding="utf-8") as f:
            loaded = json.load(f)
        return _merge_defaults(loaded, _DEFAULT_SETTINGS)
    except (json.JSONDecodeError, OSError):
        return _deep_copy(_DEFAULT_SETTINGS)


def save_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Sauvegarde les paramètres et retourne la config finale (fusionnée avec les défauts)."""
    merged = _merge_defaults(settings, _DEFAULT_SETTINGS)
    _ensure_dir()
    with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    return merged


def _deep_copy(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _deep_copy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deep_copy(v) for v in obj]
    return obj


def _merge_defaults(loaded: dict, defaults: dict) -> dict:
    """Fusionne les valeurs chargées avec les défauts (récursif)."""
    result = _deep_copy(defaults)
    for key, value in loaded.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_defaults(value, result[key])
        elif key in result:
            result[key] = value
    return result
