"""
Graphe RAG minimal : retrieval + génération.
Un seul chemin d'exécution (_retrieve puis _generate), avec ou sans Langgraph.
Utilise document_store et un LLM optionnel (OpenAI si clé fournie).
"""
import os
from typing import Any

from app.services.document_store import get_all_chunks
from app.services.settings_service import get_settings
from app.services import vector_store

# Langchain/Langgraph optionnels pour éviter erreurs si pas de clé API
try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
    _HAS_LLM = True
except ImportError:
    _HAS_LLM = False


def _get_llm():
    if not _HAS_LLM:
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    settings = get_settings()
    chat_cfg = settings.get("chat", {})
    model = chat_cfg.get("model", "gpt-4o-mini")
    temperature = float(chat_cfg.get("temperature", 0))
    return ChatOpenAI(model=model, temperature=temperature)


def _retrieve(state: dict) -> dict:
    """Récupère les chunks pertinents : recherche sémantique (embeddings) ou fallback mot-clé."""
    question = state.get("question", "")
    settings = get_settings()
    k = int(settings.get("retriever", {}).get("k", 5))
    k = max(1, min(k, 20))
    if vector_store.is_available():
        with_scores = vector_store.similarity_search_with_scores(question, k=k)
        state["retrieved_chunks"] = with_scores
        state["retrieval_method"] = "similarity"
        state["context"] = "\n\n".join(c["text"] for c in with_scores) if with_scores else ""
    else:
        chunks = get_all_chunks()
        if question and chunks:
            q_lower = question.lower()
            relevant = [c for c in chunks if any(w in c.lower() for w in q_lower.split() if len(w) > 2)]
            raw = relevant[:k] if relevant else chunks[:k]
        else:
            raw = chunks[:k] if chunks else []
        state["retrieved_chunks"] = [{"text": t, "score": None} for t in raw]
        state["retrieval_method"] = "keyword"
        state["context"] = "\n\n".join(raw) if raw else ""
    return state


def _generate(state: dict) -> dict:
    """Génère la réponse avec le LLM ou un fallback."""
    context = state.get("context", "")
    question = state.get("question", "")
    llm = _get_llm()
    if llm and (context or question):
        system = "Tu réponds à la question en t'appuyant sur le contexte fourni. Si le contexte est vide, dis que tu n'as pas d'information."
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=f"Contexte:\n{context}\n\nQuestion: {question}"),
        ]
        response = llm.invoke(messages)
        state["answer"] = response.content if hasattr(response, "content") else str(response)
    else:
        all_chunks = get_all_chunks()
        if not all_chunks:
            state["answer"] = "Aucun document ingéré. Uploadez un PDF ou un fichier texte via /api/rag/ingest."
        else:
            state["answer"] = f"Contexte disponible ({len(all_chunks)} chunks). Configurez OPENAI_API_KEY pour des réponses générées."
    state["sources"] = state.get("context", "").split("\n\n")[:3] if state.get("context") else []
    return state


def _run_rag_pipeline(state: dict) -> dict:
    """Exécute retrieve puis generate. Chemin unique pour avec/sans Langgraph."""
    state = _retrieve(state)
    state = _generate(state)
    return state


async def query_rag(question: str) -> dict[str, Any]:
    """Exécute le pipeline RAG et retourne answer, sources, retrieved_chunks, retrieval_method."""
    state = {
        "question": question,
        "context": "",
        "answer": "",
        "sources": [],
        "retrieved_chunks": [],
        "retrieval_method": "keyword",
    }
    state = _run_rag_pipeline(state)
    return {
        "answer": state.get("answer", ""),
        "sources": state.get("sources", []),
        "retrieved_chunks": state.get("retrieved_chunks", []),
        "retrieval_method": state.get("retrieval_method", "keyword"),
    }
