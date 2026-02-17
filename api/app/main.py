"""
Point d'entrée FastAPI pour l'API Langgraph-RAG.
CORS + garde frontend (Origin/Referer + option clé API) pour limiter l'accès au front.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Charger api/.env (fonctionne que uvicorn soit lancé depuis api/ ou la racine du projet)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.frontend_guard import FrontendGuardMiddleware
from app.routes import health, rag, settings

app = FastAPI(
    title="Langgraph-RAG API",
    description="API RAG avec Langgraph et Docling",
    version="0.1.0",
)

# Origines autorisées : dev local + GitHub Pages (à personnaliser selon votre compte)
_front_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
# En prod, ajouter par ex. https://votreuser.github.io
if origin := os.getenv("GITHUB_PAGES_ORIGIN"):
    _front_origins.append(origin.strip())
_front_origins = [o.strip() for o in _front_origins if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_front_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Garde frontend : rejette les requêtes sans Origin/Referer autorisé (curl, Postman, etc.)
# et optionnellement exige X-API-Key si FRONTEND_API_KEY est défini
_require_origin = os.getenv("REQUIRE_ORIGIN_CHECK", "").lower() in ("1", "true", "yes")
if not _require_origin and os.getenv("GITHUB_PAGES_ORIGIN"):
    _require_origin = True  # en prod (origine GitHub Pages définie), activer par défaut
app.add_middleware(
    FrontendGuardMiddleware,
    allowed_origins=_front_origins,
    require_origin_check=_require_origin,
    api_key=os.getenv("FRONTEND_API_KEY"),
)

app.include_router(health.router, tags=["health"])
app.include_router(rag.router, prefix="/api/rag", tags=["rag"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])


@app.get("/")
async def root():
    return {"message": "Langgraph-RAG API", "docs": "/docs"}
