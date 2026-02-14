"""Routes RAG : ingestion de documents et requêtes."""
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

from app.services.docling_ingest import (
    ingest_document_with_id,
    ingest_document,
    list_documents,
    get_chunks_by_document_id,
    delete_document,
)
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
        doc_id, chunks = await ingest_document(content, filename=file.filename)
        return {"id": doc_id, "filename": file.filename, "chunks": len(chunks)}
    except Exception as e:
        raise HTTPException(422, f"Erreur d'ingestion: {e!s}") from e


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
        raise HTTPException(422, f"Erreur de ré-ingestion: {e!s}") from e


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
