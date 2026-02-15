"""Tests du pipeline RAG (retrieve + generate) avec mocks."""
from unittest.mock import patch

import pytest

from app.services import rag_graph


@pytest.mark.asyncio
async def test_query_rag_returns_keys():
    """query_rag retourne answer, sources, retrieved_chunks, retrieval_method."""
    with patch.object(rag_graph, "vector_store") as vs:
        vs.is_available.return_value = False
    with patch.object(rag_graph, "get_all_chunks", return_value=[]):
        with patch.object(rag_graph, "_get_llm", return_value=None):
            result = await rag_graph.query_rag("Une question ?")
    assert "answer" in result
    assert "sources" in result
    assert "retrieved_chunks" in result
    assert "retrieval_method" in result
    assert result["retrieval_method"] in ("keyword", "similarity")


@pytest.mark.asyncio
async def test_query_rag_no_documents_message():
    """Sans document ingéré, la réponse indique d'uploader un document."""
    with patch.object(rag_graph, "vector_store") as vs:
        vs.is_available.return_value = False
    with patch.object(rag_graph, "get_all_chunks", return_value=[]):
        with patch.object(rag_graph, "_get_llm", return_value=None):
            result = await rag_graph.query_rag("Question")
    assert "Aucun document ingéré" in result["answer"] or "Uploadez" in result["answer"]


@pytest.mark.asyncio
async def test_query_rag_keyword_fallback_uses_chunks():
    """Sans vector store, le retrieval mot-clé utilise get_all_chunks."""
    with patch.object(rag_graph, "vector_store") as vs:
        vs.is_available.return_value = False
    with patch.object(rag_graph, "get_all_chunks", return_value=["contenu pertinent"]) as gac:
        with patch.object(rag_graph, "_get_llm", return_value=None):
            result = await rag_graph.query_rag("pertinent")
    gac.assert_called()
    assert result["retrieval_method"] == "keyword"
    assert len(result["retrieved_chunks"]) >= 0
