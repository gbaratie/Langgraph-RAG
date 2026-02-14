"""
Ingestion de documents avec Docling (PDF, Word, etc.).
Produit des chunks de texte pour le RAG.
"""
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

# Docling peut être lourd ; import conditionnel pour éviter erreurs si non installé
try:
    from docling.document_converter import DocumentConverter
except ImportError:
    DocumentConverter = None  # type: ignore


class IngestedDocument:
    """Un document ingéré avec son identifiant et ses chunks."""

    def __init__(self, doc_id: str, filename: str, chunks: List[str]):
        self.id = doc_id
        self.filename = filename
        self.chunks = list(chunks)

    def to_dict(self) -> dict:
        return {"id": self.id, "filename": self.filename, "chunk_count": len(self.chunks)}


# Stockage en mémoire : liste de documents (à remplacer par une DB en prod)
_documents: List[IngestedDocument] = []


def get_ingested_chunks() -> List[str]:
    """Retourne tous les chunks de tous les documents (pour le retrieval)."""
    result: List[str] = []
    for doc in _documents:
        result.extend(doc.chunks)
    return result


def list_documents() -> List[dict]:
    """Retourne la liste des documents ingérés (id, filename, chunk_count)."""
    return [d.to_dict() for d in _documents]


def get_chunks_by_document_id(doc_id: str) -> Optional[List[str]]:
    """Retourne les chunks d'un document ou None si inconnu."""
    for doc in _documents:
        if doc.id == doc_id:
            return list(doc.chunks)
    return None


def delete_document(doc_id: str) -> bool:
    """Supprime un document par son id. Retourne True si supprimé."""
    global _documents
    for i, doc in enumerate(_documents):
        if doc.id == doc_id:
            _documents = _documents[:i] + _documents[i + 1 :]
            return True
    return False


async def ingest_document(content: bytes, filename: str = "document") -> tuple[str, List[str]]:
    """Parse le document avec Docling et retourne (doc_id, chunks)."""
    doc_id = str(uuid.uuid4())
    if DocumentConverter is None:
        # Fallback sans Docling : traiter comme texte brut (pour dev sans installer Docling)
        text = content.decode("utf-8", errors="replace")
        chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
    else:
        converter = DocumentConverter()
        suffix = Path(filename).suffix or ".bin"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            result = converter.convert(tmp_path)
            doc = result.document
            text = doc.export_to_markdown() or (getattr(doc, "export_to_text", lambda: None)() or "")
        finally:
            Path(tmp_path).unlink(missing_ok=True)
        chunks = [p.strip() for p in text.split("\n\n") if p.strip()]

    _documents.append(IngestedDocument(doc_id=doc_id, filename=filename, chunks=chunks))
    return doc_id, chunks
