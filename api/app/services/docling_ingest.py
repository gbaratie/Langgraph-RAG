"""
Ingestion de documents avec Docling (PDF, Word, etc.).
Produit des chunks de texte pour le RAG.
"""
import io
import tempfile
from pathlib import Path
from typing import List

# Docling peut être lourd ; import conditionnel pour éviter erreurs si non installé
try:
    from docling.document_converter import DocumentConverter
except ImportError:
    DocumentConverter = None  # type: ignore


# Stockage en mémoire des chunks (première version ; à remplacer par un vecteur DB en prod)
_ingested_chunks: List[str] = []


async def ingest_document(content: bytes, filename: str = "document") -> List[str]:
    """Parse le document avec Docling et retourne une liste de chunks texte."""
    if DocumentConverter is None:
        # Fallback sans Docling : traiter comme texte brut (pour dev sans installer Docling)
        text = content.decode("utf-8", errors="replace")
        chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
        _ingested_chunks.extend(chunks)
        return chunks

    converter = DocumentConverter()
    # Docling convert() attend un chemin, une URL ou un DocumentStream ; on utilise un fichier temporaire
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
    _ingested_chunks.extend(chunks)
    return chunks


def get_ingested_chunks() -> List[str]:
    """Retourne tous les chunks ingérés (pour le retrieval simple)."""
    return list(_ingested_chunks)
