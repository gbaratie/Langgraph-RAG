"""
Ingestion de documents avec Docling (PDF, Word, etc.).
Produit des chunks de texte pour le RAG.
"""
import tempfile
import uuid
from pathlib import Path
from typing import Any, AsyncIterator, List, Optional

from app.services.settings_service import get_settings
from app.services import vector_store

# Docling peut être lourd ; import conditionnel pour éviter erreurs si non installé
try:
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
except ImportError:
    DocumentConverter = None  # type: ignore
    PdfFormatOption = None  # type: ignore
    PdfPipelineOptions = None  # type: ignore
    TableFormerMode = None  # type: ignore
    InputFormat = None  # type: ignore

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    RecursiveCharacterTextSplitter = None  # type: ignore


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
    """Retourne tous les chunks de tous les documents (pour le retrieval fallback sans embeddings)."""
    if vector_store.is_available():
        ids = vector_store.list_document_ids()
        result: List[str] = []
        for doc_id, _ in ids:
            chunks = vector_store.get_chunks_by_doc_id(doc_id)
            if chunks:
                result.extend(chunks)
        return result
    result = []
    for doc in _documents:
        result.extend(doc.chunks)
    return result


def list_documents() -> List[dict]:
    """Retourne la liste des documents ingérés (id, filename, chunk_count)."""
    if vector_store.is_available():
        ids = vector_store.list_document_ids()
        return [
            {"id": doc_id, "filename": filename, "chunk_count": vector_store.get_chunk_count_by_doc_id(doc_id)}
            for doc_id, filename in ids
        ]
    return [d.to_dict() for d in _documents]


def get_chunks_by_document_id(doc_id: str) -> Optional[List[str]]:
    """Retourne les chunks d'un document ou None si inconnu."""
    if vector_store.is_available():
        return vector_store.get_chunks_by_doc_id(doc_id)
    for doc in _documents:
        if doc.id == doc_id:
            return list(doc.chunks)
    return None


def delete_document(doc_id: str) -> bool:
    """Supprime un document par son id. Retourne True si supprimé."""
    if vector_store.is_available():
        return vector_store.delete_by_doc_id(doc_id)
    global _documents
    for i, doc in enumerate(_documents):
        if doc.id == doc_id:
            _documents = _documents[:i] + _documents[i + 1 :]
            return True
    return False


def _split_text(text: str) -> List[str]:
    """Découpe le texte en chunks selon la configuration."""
    settings = get_settings()
    chunk_cfg = settings.get("chunks", {})
    chunk_size = chunk_cfg.get("chunk_size", 1000)
    chunk_overlap = chunk_cfg.get("chunk_overlap", 200)
    separators = chunk_cfg.get("separators", ["\n\n", "\n", " ", ""])

    if not isinstance(separators, list) or len(separators) == 0:
        separators = ["\n\n", "\n", " ", ""]

    if RecursiveCharacterTextSplitter is not None:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
        )
        chunks = splitter.split_text(text)
    else:
        chunks = [p.strip() for p in text.split("\n\n") if p.strip()]

    return chunks


def _build_document_converter():
    """Construit le DocumentConverter avec les options Docling configurées."""
    if DocumentConverter is None:
        return None

    settings = get_settings()
    docling_cfg = settings.get("docling", {})

    format_options = {}
    try:
        if PdfFormatOption is not None and PdfPipelineOptions is not None and InputFormat is not None:
            pipeline_opts = PdfPipelineOptions(
                do_table_structure=docling_cfg.get("do_table_structure", True),
                enable_remote_services=docling_cfg.get("enable_remote_services", False),
                artifacts_path=docling_cfg.get("artifacts_path") or None,
            )
            if hasattr(pipeline_opts, "table_structure_options"):
                pipeline_opts.table_structure_options.do_cell_matching = docling_cfg.get(
                    "do_cell_matching", True
                )
                mode_str = docling_cfg.get("table_former_mode", "ACCURATE")
                if TableFormerMode is not None and hasattr(TableFormerMode, mode_str):
                    pipeline_opts.table_structure_options.mode = getattr(
                        TableFormerMode, mode_str, TableFormerMode.ACCURATE
                    )
            format_options[InputFormat.PDF] = PdfFormatOption(pipeline_options=pipeline_opts)
    except Exception:
        pass  # Fallback au converter par défaut

    if format_options:
        return DocumentConverter(format_options=format_options)
    return DocumentConverter()


async def _convert_and_chunk(content: bytes, filename: str) -> str:
    """Convertit le document en texte markdown via Docling."""
    suffix = Path(filename).suffix or ".bin"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        converter = _build_document_converter()
        if converter is None:
            return content.decode("utf-8", errors="replace")

        settings = get_settings()
        docling_cfg = settings.get("docling", {})
        max_num_pages = docling_cfg.get("max_num_pages")
        max_file_size = docling_cfg.get("max_file_size")
        convert_kwargs = {}
        if max_num_pages is not None:
            convert_kwargs["max_num_pages"] = max_num_pages
        if max_file_size is not None:
            convert_kwargs["max_file_size"] = int(max_file_size) * 1024 * 1024  # Mo -> octets

        result = converter.convert(tmp_path, **convert_kwargs)
        doc = result.document
        return doc.export_to_markdown() or (
            getattr(doc, "export_to_text", lambda: None)() or ""
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)


async def ingest_document(
    content: bytes, filename: str = "document", doc_id: Optional[str] = None
) -> tuple[str, List[str]]:
    """Parse le document avec Docling et retourne (doc_id, chunks)."""
    if doc_id is None:
        doc_id = str(uuid.uuid4())

    text = await _convert_and_chunk(content, filename)
    chunks = _split_text(text)

    # Si doc_id existant (ré-import), supprimer l'ancien document
    delete_document(doc_id)

    if vector_store.is_available():
        vector_store.add_chunks(doc_id, filename, chunks)
    else:
        _documents.append(IngestedDocument(doc_id=doc_id, filename=filename, chunks=chunks))
    return doc_id, chunks


async def ingest_document_with_id(
    content: bytes, filename: str, doc_id: str
) -> tuple[str, List[str]]:
    """Ré-ingère un document en remplaçant l'existant (même doc_id)."""
    return await ingest_document(content, filename, doc_id)


async def ingest_document_stream(
    content: bytes, filename: str = "document", doc_id: Optional[str] = None
) -> AsyncIterator[dict[str, Any]]:
    """
    Ingère un document en émettant des statuts intermédiaires (step, message).
    Yield des dicts avec au moins "step" et "message"; le dernier a "step": "done" et "doc_id", "chunks".
    """
    if doc_id is None:
        doc_id = str(uuid.uuid4())
    try:
        yield {"step": "convert", "message": "Conversion du document (Docling)…"}
        text = await _convert_and_chunk(content, filename)
        yield {"step": "split", "message": "Découpage en chunks…"}
        chunks = _split_text(text)
        yield {"step": "split_done", "message": f"Découpage terminé ({len(chunks)} chunk(s))"}
        yield {"step": "store", "message": "Enregistrement (Chroma)…" if vector_store.is_available() else "Enregistrement en mémoire…"}
        delete_document(doc_id)
        if vector_store.is_available():
            vector_store.add_chunks(doc_id, filename, chunks)
        else:
            _documents.append(IngestedDocument(doc_id=doc_id, filename=filename, chunks=chunks))
        yield {"step": "done", "message": "Import terminé", "doc_id": doc_id, "chunks": len(chunks)}
    except Exception as e:
        yield {"step": "error", "message": str(e)}
