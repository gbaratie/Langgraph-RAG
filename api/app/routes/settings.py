"""Routes de gestion des paramètres (chunks, Docling)."""
from fastapi import APIRouter, HTTPException

from app.services.settings_service import get_settings, save_settings

router = APIRouter()


@router.get("")
async def settings_get():
    """Retourne la configuration actuelle (chunks + Docling)."""
    return get_settings()


@router.put("")
async def settings_update(settings: dict):
    """Met à jour les paramètres (fusion partielle avec les défauts)."""
    try:
        return save_settings(settings)
    except Exception as e:
        raise HTTPException(422, f"Paramètres invalides: {e!s}") from e
