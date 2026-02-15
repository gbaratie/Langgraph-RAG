"""Routes RAG : ingestion de documents et requêtes."""
from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.docling_ingest import (
    ingest_document_with_id,
    ingest_document,
    ingest_document_stream,
    list_documents,
    get_chunks_by_document_id,
    delete_document,
)
from app.services.rag_graph import query_rag
from app.services import vector_store

router = APIRouter()
_log = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    question: str


class RetrievedChunk(BaseModel):
    text: str
    score: Optional[float] = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[str] = []
    retrieved_chunks: list[RetrievedChunk] = []
    retrieval_method: str = "keyword"


@router.post("/ingest", status_code=201)
async def ingest(file: UploadFile = File(...)):
    """Ingère un document (PDF, etc.) via Docling et l'ajoute au contexte RAG."""
    if not file.filename:
        raise HTTPException(400, "Nom de fichier manquant")
    content = await file.read()
    try:
        doc_id, chunks = await ingest_document(content, filename=file.filename)
        return {"id": doc_id, "filename": file.filename, "chunks": len(chunks)}
    except Exception as e:
        _log.exception("Erreur d'ingestion: %s", e)
        raise HTTPException(422, "Erreur d'ingestion du document") from e


@router.post("/ingest-stream")
async def ingest_stream(file: UploadFile = File(...)):
    """Ingère un document en streamant les statuts (SSE)."""
    if not file.filename:
        raise HTTPException(400, "Nom de fichier manquant")
    content = await file.read()

    async def event_stream():
        async for event in ingest_document_stream(content, filename=file.filename):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/vector-map")
async def vector_map():
    """Retourne les points pour la carte 2D des vecteurs (t-SNE)."""
    available = vector_store.is_available()
    points = vector_store.get_vector_map_points() if available else []
    return {"available": available, "points": points}


@router.get("/documents")
async def documents_list():
    """Liste les documents ingérés (id, filename, chunk_count)."""
    return list_documents()


@router.get("/documents/{doc_id}/chunks")
async def documents_chunks(doc_id: str):
    """Retourne les chunks d'un document."""
    chunks = get_chunks_by_document_id(doc_id)
    if chunks is None:
        raise HTTPException(404, "Document non trouvé")
    return {"id": doc_id, "chunks": chunks}


@router.delete("/documents/{doc_id}")
async def documents_delete(doc_id: str):
    """Supprime un document et ses chunks."""
    if not delete_document(doc_id):
        raise HTTPException(404, "Document non trouvé")
    return {"ok": True}


@router.post("/documents/{doc_id}/reingest", status_code=200)
async def documents_reingest(doc_id: str, file: UploadFile = File(...)):
    """Ré-ingère un document avec les paramètres actuels (remplace l'existant)."""
    if not file.filename:
        raise HTTPException(400, "Nom de fichier manquant")
    if get_chunks_by_document_id(doc_id) is None:
        raise HTTPException(404, "Document non trouvé")
    content = await file.read()
    try:
        _, chunks = await ingest_document_with_id(content, file.filename, doc_id)
        return {"id": doc_id, "filename": file.filename, "chunks": len(chunks)}
    except Exception as e:
        _log.exception("Erreur de ré-ingestion: %s", e)
        raise HTTPException(422, "Erreur de ré-ingestion du document") from e


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Pose une question au RAG (retrieval + LLM)."""
    if not req.question.strip():
        raise HTTPException(400, "Question vide")
    try:
        result = await query_rag(req.question)
        return QueryResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            retrieved_chunks=result.get("retrieved_chunks", []),
            retrieval_method=result.get("retrieval_method", "keyword"),
        )
    except Exception as e:
        _log.exception("Erreur RAG: %s", e)
        raise HTTPException(500, "Erreur lors de la requête RAG") from e
