"""
Service de gestion des paramètres (chunks, Docling).
Stockage dans data/settings.json. Validation via schéma Pydantic.
"""
import json
from pathlib import Path
from typing import Any

from app.schemas.settings import AppSettings

# Chemin relatif au dossier api/
_SETTINGS_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_SETTINGS_FILE = _SETTINGS_DIR / "settings.json"


def _ensure_dir() -> None:
    _SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


def get_settings() -> dict[str, Any]:
    """Charge les paramètres depuis le fichier, ou retourne les valeurs par défaut (validées)."""
    if not _SETTINGS_FILE.exists():
        return AppSettings().model_dump()
    try:
        with open(_SETTINGS_FILE, encoding="utf-8") as f:
            loaded = json.load(f)
        # Valider et fusionner avec les défauts (Pydantic remplit les champs manquants)
        settings = AppSettings.model_validate(loaded)
        return settings.model_dump()
    except (json.JSONDecodeError, OSError, ValueError):
        return AppSettings().model_dump()


def _deep_merge(base: dict, override: dict) -> dict:
    """Fusionne override dans base (récursif). Les clés absentes de override sont conservées."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def save_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """
    Valide les paramètres avec le schéma, sauvegarde uniquement les clés autorisées,
    et retourne la config finale (fusionnée avec les défauts).
    """
    validated = AppSettings.model_validate(settings)
    merged = validated.model_dump()
    _ensure_dir()
    with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    return merged


def update_settings(partial: dict[str, Any]) -> dict[str, Any]:
    """
    Met à jour partiellement la config : fusionne partial avec la config actuelle,
    valide le tout et sauvegarde. Idéal pour PUT avec un body partiel.
    """
    current = get_settings()
    merged = _deep_merge(current, partial)
    return save_settings(merged)
