"""Routes de gestion des paramètres (chunks, Docling)."""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.services.settings_service import get_settings, update_settings

router = APIRouter()
_log = logging.getLogger(__name__)


@router.get("")
async def settings_get():
    """Retourne la configuration actuelle (chunks + Docling)."""
    return get_settings()


@router.put("")
async def settings_update(settings: dict):
    """Met à jour les paramètres (fusion partielle avec la config actuelle)."""
    try:
        return update_settings(settings)
    except ValidationError as e:
        _log.warning("Paramètres invalides: %s", e)
        raise HTTPException(422, "Paramètres invalides") from e
    except Exception as e:
        _log.exception("Erreur lors de la sauvegarde des paramètres: %s", e)
        raise HTTPException(500, "Erreur serveur lors de la sauvegarde") from e
