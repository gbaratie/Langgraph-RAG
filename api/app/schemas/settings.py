"""
Schéma Pydantic pour la configuration (chunks, Docling, retriever, chat).
Seules les clés définies ici sont acceptées et persistées.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class ChunksSettings(BaseModel):
    chunk_size: int = Field(default=1000, ge=100, le=10000)
    chunk_overlap: int = Field(default=200, ge=0, le=2000)
    separators: List[str] = Field(default=["\n\n", "\n", " ", ""], min_length=1)


class DoclingSettings(BaseModel):
    max_num_pages: Optional[int] = Field(default=None, ge=1, le=10000)
    max_file_size: Optional[int] = Field(default=None, ge=1, le=500)  # Mo
    do_table_structure: bool = True
    do_cell_matching: bool = True
    table_former_mode: str = Field(default="ACCURATE", pattern="^(ACCURATE|FAST)$")
    enable_remote_services: bool = False
    artifacts_path: Optional[str] = None


class RetrieverSettings(BaseModel):
    k: int = Field(default=5, ge=1, le=20)


class ChatSettings(BaseModel):
    model: str = Field(default="gpt-4o-mini", min_length=1)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


class AppSettings(BaseModel):
    """Configuration complète de l'application. Seules ces sections sont autorisées."""

    chunks: ChunksSettings = Field(default_factory=ChunksSettings)
    docling: DoclingSettings = Field(default_factory=DoclingSettings)
    retriever: RetrieverSettings = Field(default_factory=RetrieverSettings)
    chat: ChatSettings = Field(default_factory=ChatSettings)
