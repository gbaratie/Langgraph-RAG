"""
Middleware pour restreindre l'accès à l'API aux requêtes venant du frontend autorisé.

- Vérification Origin/Referer : rejette les requêtes sans en-tête Origin ou Referer
  autorisé (bloque curl, Postman, scripts). Contournable par un attaquant qui spoof
  les en-têtes, mais bloque l'usage direct de l'URL par des tiers.
- Option clé API (X-API-Key) : si FRONTEND_API_KEY est défini, les requêtes doivent
  contenir ce header. Sur GitHub Pages la clé est visible dans le front ; utile pour
  rotation et rate limiting, pas une sécurité forte.
"""
from __future__ import annotations

import os
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


# Chemins exclus de la vérification (health check Render, docs, racine)
SKIP_PATHS = {"", "/", "/docs", "/redoc", "/openapi.json", "/health"}


def _get_origin_from_referer(referer: str) -> str | None:
    """Extrait l'origine (scheme + host) d'un Referer."""
    try:
        parsed = urlparse(referer)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        pass
    return None


def _normalize_origin(origin: str) -> str:
    """Retire le slash final pour comparaison."""
    return origin.rstrip("/") if origin else ""


class FrontendGuardMiddleware(BaseHTTPMiddleware):
    """
    Vérifie que la requête provient d'une origine autorisée (Origin/Referer)
    et optionnellement d'une clé API valide.
    """

    def __init__(
        self,
        app,
        allowed_origins: list[str],
        require_origin_check: bool = True,
        api_key: str | None = None,
        skip_paths: set[str] | None = None,
    ):
        super().__init__(app)
        self.allowed_origins = {_normalize_origin(o) for o in allowed_origins if o.strip()}
        self.require_origin_check = require_origin_check
        self.api_key = (api_key or "").strip() or None
        self.skip_paths = skip_paths or SKIP_PATHS

    def _path_skipped(self, path: str) -> bool:
        return path in self.skip_paths or path.rstrip("/") in self.skip_paths

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if self._path_skipped(path):
            return await call_next(request)
        # Laisser passer les preflight CORS (OPTIONS) sans vérifier la clé
        if request.method == "OPTIONS":
            return await call_next(request)

        # Option : clé API
        if self.api_key:
            key = request.headers.get("X-API-Key", "").strip()
            if key != self.api_key:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Clé API invalide ou manquante"},
                )

        # Vérification Origin / Referer (requêtes type navigateur)
        if self.require_origin_check and self.allowed_origins:
            origin = request.headers.get("Origin", "").strip()
            referer = request.headers.get("Referer", "").strip()
            request_origin = _normalize_origin(origin) or (
                _get_origin_from_referer(referer) or ""
            )
            if not request_origin or request_origin not in self.allowed_origins:
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Origine non autorisée. Seul le frontend configuré peut appeler cette API."
                    },
                )

        return await call_next(request)
