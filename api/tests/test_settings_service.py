"""Tests du service de paramètres (validation, merge, lecture/écriture)."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

# Conftest a ajouté api/ au path
from app.schemas.settings import AppSettings, ChunksSettings
from app.services import settings_service


@pytest.fixture
def temp_settings_dir(tmp_path):
    """Utilise un répertoire temporaire pour settings.json."""
    settings_dir = tmp_path / "data"
    settings_dir.mkdir()
    settings_file = settings_dir / "settings.json"
    with patch.object(settings_service, "_SETTINGS_DIR", settings_dir):
        with patch.object(settings_service, "_SETTINGS_FILE", settings_file):
            yield settings_file


def test_app_settings_defaults():
    """Les valeurs par défaut sont valides."""
    s = AppSettings()
    assert s.chunks.chunk_size == 1000
    assert s.chunks.chunk_overlap == 200
    assert s.retriever.k == 5
    assert s.chat.model == "gpt-4o-mini"


def test_app_settings_validate_rejects_invalid():
    """Validation rejette chunk_size hors bornes."""
    with pytest.raises(ValidationError):
        AppSettings(chunks=ChunksSettings(chunk_size=50))  # < 100
    with pytest.raises(ValidationError):
        AppSettings(chunks=ChunksSettings(chunk_overlap=-1))


def test_get_settings_returns_dict(temp_settings_dir):
    """get_settings retourne un dict avec les clés attendues."""
    temp_settings_dir.write_text("{}", encoding="utf-8")
    out = settings_service.get_settings()
    assert isinstance(out, dict)
    assert "chunks" in out
    assert "docling" in out
    assert "retriever" in out
    assert "chat" in out
    assert out["chunks"]["chunk_size"] == 1000


def test_get_settings_merge_partial_file(temp_settings_dir):
    """get_settings fusionne le fichier partiel avec les défauts."""
    temp_settings_dir.write_text(
        '{"chunks": {"chunk_size": 500}}',
        encoding="utf-8",
    )
    out = settings_service.get_settings()
    assert out["chunks"]["chunk_size"] == 500
    assert out["chunks"]["chunk_overlap"] == 200
    assert out["retriever"]["k"] == 5


def test_save_settings_valid(temp_settings_dir):
    """save_settings valide et persiste."""
    payload = {"chunks": {"chunk_size": 800, "chunk_overlap": 100}}
    result = settings_service.save_settings(payload)
    assert result["chunks"]["chunk_size"] == 800
    assert result["chunks"]["chunk_overlap"] == 100
    assert temp_settings_dir.exists()
    loaded = json.loads(temp_settings_dir.read_text(encoding="utf-8"))
    assert loaded["chunks"]["chunk_size"] == 800


def test_save_settings_rejects_invalid():
    """save_settings lève sur payload invalide."""
    with pytest.raises(ValidationError):
        settings_service.save_settings({"chunks": {"chunk_size": -1}})


def test_update_settings_merge_partial(temp_settings_dir):
    """update_settings fusionne avec la config actuelle."""
    temp_settings_dir.write_text(
        '{"chunks": {"chunk_size": 1000}, "retriever": {"k": 5}}',
        encoding="utf-8",
    )
    result = settings_service.update_settings({"chunks": {"chunk_size": 600}})
    assert result["chunks"]["chunk_size"] == 600
    assert result["retriever"]["k"] == 5
