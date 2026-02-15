"""Tests du document_store (mémoire quand vector_store indisponible)."""
from unittest.mock import patch, MagicMock

import pytest

from app.services import document_store


@pytest.fixture(autouse=True)
def force_memory_backend():
    """Force l'utilisation du stockage en mémoire (pas de Chroma)."""
    with patch.object(document_store, "_uses_vector_store", return_value=False):
        # Réinitialiser la liste en mémoire entre tests
        document_store._memory_documents.clear()
        yield


def test_list_documents_empty():
    """Liste vide au départ."""
    assert document_store.list_documents() == []


def test_add_document_then_list():
    """Après add_document, list_documents retourne le document."""
    document_store.add_document("doc1", "f1.pdf", ["chunk1", "chunk2"])
    docs = document_store.list_documents()
    assert len(docs) == 1
    assert docs[0]["id"] == "doc1"
    assert docs[0]["filename"] == "f1.pdf"
    assert docs[0]["chunk_count"] == 2


def test_get_chunks_by_doc_id():
    """get_chunks_by_doc_id retourne les chunks ou None."""
    assert document_store.get_chunks_by_doc_id("nonexistent") is None
    document_store.add_document("d1", "f.txt", ["a", "b"])
    assert document_store.get_chunks_by_doc_id("d1") == ["a", "b"]


def test_delete_document():
    """delete_document retire le document."""
    document_store.add_document("d1", "f.txt", ["x"])
    assert document_store.delete_document("d1") is True
    assert document_store.list_documents() == []
    assert document_store.get_chunks_by_doc_id("d1") is None
    assert document_store.delete_document("d1") is False


def test_get_all_chunks():
    """get_all_chunks agrège tous les chunks."""
    document_store.add_document("d1", "f1", ["c1"])
    document_store.add_document("d2", "f2", ["c2", "c3"])
    assert document_store.get_all_chunks() == ["c1", "c2", "c3"]


def test_add_document_replace_memory():
    """En mémoire, ré-ajouter le même doc_id remplace."""
    document_store.add_document("d1", "old.pdf", ["old_chunk"])
    document_store.add_document("d1", "new.pdf", ["new1", "new2"])
    docs = document_store.list_documents()
    assert len(docs) == 1
    assert docs[0]["filename"] == "new.pdf"
    assert docs[0]["chunk_count"] == 2
    assert document_store.get_chunks_by_doc_id("d1") == ["new1", "new2"]


def test_add_document_empty_chunks_returns_false():
    """add_document avec chunks vide retourne False."""
    assert document_store.add_document("d1", "f", []) is False
    assert document_store.list_documents() == []
