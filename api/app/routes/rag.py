"""Routes RAG : ingestion de documents et requêtes."""
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

from app.services.docling_ingest import ingest_document
from app.services.rag_graph import query_rag

router = APIRouter()


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[str] = []


@router.post("/ingest", status_code=201)
async def ingest(file: UploadFile = File(...)):
    """Ingère un document (PDF, etc.) via Docling et l'ajoute au contexte RAG."""
    if not file.filename:
        raise HTTPException(400, "Nom de fichier manquant")
    content = await file.read()
    try:
        chunks = await ingest_document(content, filename=file.filename)
        return {"filename": file.filename, "chunks": len(chunks)}
    except Exception as e:
        raise HTTPException(422, f"Erreur d'ingestion: {e!s}") from e


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Pose une question au RAG (retrieval + LLM)."""
    if not req.question.strip():
        raise HTTPException(400, "Question vide")
    try:
        result = await query_rag(req.question)
        return QueryResponse(answer=result["answer"], sources=result.get("sources", []))
    except Exception as e:
        raise HTTPException(500, f"Erreur RAG: {e!s}") from e
