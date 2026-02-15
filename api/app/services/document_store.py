"""
Abstraction du stockage des documents ingérés : Chroma (vector_store) ou mémoire.
Une seule source de vérité pour list_documents, get_chunks, add_document, delete_document.
"""
import logging
from typing import List, Optional

from app.services import vector_store

_log = logging.getLogger(__name__)


class _InMemoryDoc:
    def __init__(self, doc_id: str, filename: str, chunks: List[str]):
        self.id = doc_id
        self.filename = filename
        self.chunks = list(chunks)


# Stockage en mémoire lorsque le vector store n'est pas disponible
_memory_documents: List[_InMemoryDoc] = []


def _uses_vector_store() -> bool:
    return vector_store.is_available()


def list_documents() -> List[dict]:
    """Retourne la liste des documents (id, filename, chunk_count)."""
    if _uses_vector_store():
        ids = vector_store.list_document_ids()
        return [
            {
                "id": doc_id,
                "filename": filename,
                "chunk_count": vector_store.get_chunk_count_by_doc_id(doc_id),
            }
            for doc_id, filename in ids
        ]
    return [
        {"id": d.id, "filename": d.filename, "chunk_count": len(d.chunks)}
        for d in _memory_documents
    ]


def get_chunks_by_doc_id(doc_id: str) -> Optional[List[str]]:
    """Retourne les chunks d'un document ou None si inconnu."""
    if _uses_vector_store():
        return vector_store.get_chunks_by_doc_id(doc_id)
    for doc in _memory_documents:
        if doc.id == doc_id:
            return list(doc.chunks)
    return None


def document_exists(doc_id: str) -> bool:
    """True si le document existe."""
    return get_chunks_by_doc_id(doc_id) is not None


def delete_document(doc_id: str) -> bool:
    """Supprime un document. Retourne True si supprimé."""
    if _uses_vector_store():
        return vector_store.delete_by_doc_id(doc_id)
    global _memory_documents
    for i, doc in enumerate(_memory_documents):
        if doc.id == doc_id:
            _memory_documents = _memory_documents[:i] + _memory_documents[i + 1 :]
            return True
    return False


def add_document(doc_id: str, filename: str, chunks: List[str]) -> bool:
    """
    Ajoute ou remplace un document par son doc_id.
    En mode vector_store : remplacement atomique (écriture temporaire puis bascule)
    pour éviter de perdre l'ancien document si l'ajout échoue.
    """
    if not chunks:
        return False

    if _uses_vector_store():
        return _add_document_vector_store(doc_id, filename, chunks)
    return _add_document_memory(doc_id, filename, chunks)


def _add_document_vector_store(doc_id: str, filename: str, chunks: List[str]) -> bool:
    """Ajoute ou remplace dans Chroma avec bascule atomique si le doc existait."""
    existing = document_exists(doc_id)
    if not existing:
        ok = vector_store.add_chunks(doc_id, filename, chunks)
        return ok
    # Remplacement : écrire dans un doc temporaire, puis supprimer l'ancien, puis renommer
    temp_id = f"{doc_id}_replacing"
    if not vector_store.add_chunks(temp_id, filename, chunks):
        return False
    try:
        vector_store.delete_by_doc_id(doc_id)
    except Exception as e:
        _log.warning("Suppression de l'ancien doc %s après ajout temp a échoué: %s", doc_id, e)
        vector_store.delete_by_doc_id(temp_id)
        return False
    new_chunks = vector_store.get_chunks_by_doc_id(temp_id)
    if not new_chunks:
        _log.error("Chunks temporaires introuvables pour %s", temp_id)
        return False
    if not vector_store.add_chunks(doc_id, filename, new_chunks):
        _log.error("Échec de la copie temp -> %s", doc_id)
        vector_store.delete_by_doc_id(temp_id)
        return False
    vector_store.delete_by_doc_id(temp_id)
    return True


def _add_document_memory(doc_id: str, filename: str, chunks: List[str]) -> bool:
    """Ajoute ou remplace en mémoire."""
    global _memory_documents
    for i, doc in enumerate(_memory_documents):
        if doc.id == doc_id:
            _memory_documents = _memory_documents[:i] + _memory_documents[i + 1 :]
            break
    _memory_documents.append(_InMemoryDoc(doc_id, filename, chunks))
    return True


def get_all_chunks() -> List[str]:
    """Retourne tous les chunks de tous les documents (pour retrieval fallback sans embeddings)."""
    if _uses_vector_store():
        result: List[str] = []
        for doc_id, _ in vector_store.list_document_ids():
            chunks = vector_store.get_chunks_by_doc_id(doc_id)
            if chunks:
                result.extend(chunks)
        return result
    out: List[str] = []
    for doc in _memory_documents:
        out.extend(doc.chunks)
    return out
