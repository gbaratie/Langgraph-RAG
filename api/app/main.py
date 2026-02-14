"""
Point d'entrée FastAPI pour l'API Langgraph-RAG.
CORS configuré pour le frontend (localhost + GitHub Pages).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Charger api/.env (fonctionne que uvicorn soit lancé depuis api/ ou la racine du projet)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=_front_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(rag.router, prefix="/api/rag", tags=["rag"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])


@app.get("/")
async def root():
    return {"message": "Langgraph-RAG API", "docs": "/docs"}
