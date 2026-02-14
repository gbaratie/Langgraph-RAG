"""Route de santé pour vérifier que l'API répond."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "langgraph-rag-api"}
