"""
Stockage vectoriel Chroma pour les chunks et embeddings.
Fonctionne en local (persist_directory) et en production (même répertoire ou Chroma distant).
"""
import logging
import os
from typing import Any, List, Optional

# Import conditionnel pour ne pas casser le démarrage sans clé API
try:
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_openai import OpenAIEmbeddings
    _HAS_CHROMA = True
except ImportError:
    _HAS_CHROMA = False

_COLLECTION_NAME = "rag_chunks"
# Chemin absolu par défaut (relatif au package api) pour éviter les écarts de cwd
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DEFAULT_PERSIST_DIR = os.path.join(_BASE_DIR, "data", "chroma")
_log = logging.getLogger(__name__)


def _get_persist_directory() -> str:
    raw = os.getenv("CHROMA_PERSIST_DIR", "").strip()
    if raw:
        return os.path.abspath(raw) if not os.path.isabs(raw) else raw
    return _DEFAULT_PERSIST_DIR


def _coll_get(data: Any, key: str, default: Any = None) -> Any:
    """Lit un champ du résultat Chroma (dict ou objet avec attributs)."""
    if hasattr(data, "get") and callable(getattr(data, "get")):
        return data.get(key, default)
    return getattr(data, key, default)


def _get_embedding_function():
    """Retourne l'embedding function OpenAI ou None si indisponible."""
    if not _HAS_CHROMA:
        return None
    if not os.getenv("OPENAI_API_KEY"):
        return None
    return OpenAIEmbeddings(model="text-embedding-3-small")


def _get_vector_store():
    """Retourne l'instance Chroma ou None si désactivé (pas de clé API / import)."""
    if not _HAS_CHROMA:
        return None
    emb = _get_embedding_function()
    if emb is None:
        return None
    persist_dir = _get_persist_directory()
    try:
        return Chroma(
            collection_name=_COLLECTION_NAME,
            embedding_function=emb,
            persist_directory=persist_dir,
        )
    except Exception:
        return None


def is_available() -> bool:
    """True si le vector store est utilisable (Chroma + OpenAI embeddings)."""
    return _get_vector_store() is not None


def add_chunks(doc_id: str, filename: str, chunks: List[str]) -> bool:
    """
    Ajoute les chunks au vector store avec métadonnées doc_id, filename, chunk_index.
    Retourne True en cas de succès, False sinon.
    """
    store = _get_vector_store()
    if store is None or not chunks:
        return False
    try:
        documents = [
            Document(
                page_content=chunk,
                metadata={"doc_id": doc_id, "filename": filename, "chunk_index": i},
            )
            for i, chunk in enumerate(chunks)
        ]
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        store.add_documents(documents=documents, ids=ids)
        return True
    except Exception as e:
        _log.exception("add_chunks failed for doc_id=%s: %s", doc_id, e)
        return False


def similarity_search(question: str, k: int = 5) -> List[str]:
    """
    Recherche sémantique : retourne les textes des k chunks les plus pertinents.
    Retourne une liste vide si le store est indisponible ou en erreur.
    """
    store = _get_vector_store()
    if store is None or not question.strip():
        return []
    try:
        docs = store.similarity_search(question.strip(), k=k)
        return [d.page_content for d in docs]
    except Exception:
        return []


def similarity_search_with_scores(question: str, k: int = 5) -> List[dict[str, Any]]:
    """
    Recherche sémantique avec scores. Retourne une liste de { "text", "score" }.
    Score = distance (plus bas = plus similaire). Liste vide si indisponible.
    """
    store = _get_vector_store()
    if store is None or not question.strip():
        return []
    try:
        pairs = store.similarity_search_with_score(question.strip(), k=k)
        return [{"text": doc.page_content, "score": float(score)} for doc, score in pairs]
    except Exception as e:
        _log.debug("similarity_search_with_scores failed: %s", e)
        return []


def delete_by_doc_id(doc_id: str) -> bool:
    """Supprime tous les chunks dont la métadonnée doc_id correspond."""
    store = _get_vector_store()
    if store is None:
        return False
    try:
        collection = store._collection
        collection.delete(where={"doc_id": doc_id})
        return True
    except Exception:
        return False


def list_document_ids() -> List[tuple]:
    """
    Retourne la liste des (doc_id, filename) uniques.
    Utilise les métadonnées de la collection (agrégation côté app).
    """
    store = _get_vector_store()
    if store is None:
        return []
    try:
        collection = store._collection
        data = collection.get(include=["metadatas"])
        metadatas = _coll_get(data, "metadatas") or []
        seen: set = set()
        result: List[tuple] = []
        for m in metadatas:
            if not m:
                continue
            doc_id = m.get("doc_id")
            filename = m.get("filename", "")
            if doc_id and (doc_id, filename) not in seen:
                seen.add((doc_id, filename))
                result.append((doc_id, filename))
        return result
    except Exception:
        return []


def get_chunk_count_by_doc_id(doc_id: str) -> int:
    """Retourne le nombre de chunks pour un doc_id."""
    store = _get_vector_store()
    if store is None:
        return 0
    try:
        collection = store._collection
        data = collection.get(where={"doc_id": doc_id}, include=[])
        ids = _coll_get(data, "ids") or []
        return len(ids)
    except Exception:
        return 0


def get_chunks_by_doc_id(doc_id: str) -> Optional[List[str]]:
    """
    Retourne les chunks d'un document, triés par chunk_index.
    None si doc inconnu ou store indisponible.
    """
    store = _get_vector_store()
    if store is None:
        return None
    try:
        collection = store._collection
        data = collection.get(
            where={"doc_id": doc_id},
            include=["documents", "metadatas"],
        )
        docs = _coll_get(data, "documents") or []
        metadatas = _coll_get(data, "metadatas") or []
        if not docs:
            return None
        # Trier par chunk_index
        indexed = []
        for i, meta in enumerate(metadatas):
            idx = meta.get("chunk_index", i) if meta else i
            content = docs[i] if i < len(docs) else ""
            indexed.append((idx, content))
        indexed.sort(key=lambda x: x[0])
        return [content for _, content in indexed]
    except Exception:
        return None


def get_vector_map_points(snippet_max_len: int = 150) -> List[dict[str, Any]]:
    """
    Retourne les points pour la carte 2D des vecteurs (t-SNE sur les embeddings).
    Chaque point : id, doc_id, filename, chunk_index, text_snippet, x, y.
    Liste vide si store indisponible ou collection vide.
    """
    store = _get_vector_store()
    if store is None:
        return []
    try:
        from sklearn.manifold import TSNE
        import numpy as np

        collection = store._collection
        # include n'accepte pas "ids" en Chroma 1.5+ ; on se base sur len(embeddings)
        data = collection.get(
            include=["embeddings", "documents", "metadatas"],
        )
        ids_raw = _coll_get(data, "ids") or []
        embeddings = _coll_get(data, "embeddings") or []
        documents = _coll_get(data, "documents") or []
        metadatas = _coll_get(data, "metadatas") or []

        if not embeddings:
            _log.debug("get_vector_map_points: no embeddings")
            return []

        n = len(embeddings)
        docs = list(documents or [])
        docs = (docs + [""] * n)[:n]
        metas = list(metadatas or [])
        metas = (metas + [{}] * n)[:n]
        base_ids = list(ids_raw) if ids_raw else []
        ids_list = [base_ids[i] if i < len(base_ids) else f"chunk_{i}" for i in range(n)]

        X = np.array(embeddings, dtype=np.float64)
        tsne = TSNE(n_components=2, random_state=42)
        coords = tsne.fit_transform(X)

        points: List[dict[str, Any]] = []
        for i in range(n):
            text = docs[i] if i < len(docs) else ""
            meta = metas[i] if i < len(metas) else {}
            snippet = (text[:snippet_max_len] + "…") if len(text) > snippet_max_len else text
            points.append({
                "id": ids_list[i],
                "doc_id": meta.get("doc_id", ""),
                "filename": meta.get("filename", ""),
                "chunk_index": meta.get("chunk_index", i),
                "text_snippet": snippet,
                "x": float(coords[i, 0]),
                "y": float(coords[i, 1]),
            })
        return points
    except Exception as e:
        _log.exception("get_vector_map_points failed: %s", e)
        return []
