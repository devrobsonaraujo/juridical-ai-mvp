import math
import uuid

import pytest

from app.services.chunking_service import chunk_segments
from app.services.postgres_vector_service import (
    _validate_owner,
    _vector_literal,
)


def test_chunking_preserva_timestamps_e_texto():
    segments = [
        {"text": "primeiro segundo", "start": 0, "end": 2},
        {"text": "terceiro quarto", "start": 2, "end": 4},
    ]
    chunks = chunk_segments(segments, max_words=3, overlap_words=1)
    assert chunks == [
        {"text": "primeiro segundo terceiro quarto", "start": 0.0, "end": 4.0},
        {"text": "quarto", "start": 4.0, "end": 4.0},
    ]


def test_chunking_ignora_segmentos_vazios():
    assert chunk_segments([{"text": "  ", "start": 0, "end": 1}]) == []


def test_owner_valido():
    owner = str(uuid.uuid4())
    assert _validate_owner(owner) == owner


@pytest.mark.parametrize("owner", [None, "", "não-é-uuid", "123"])
def test_owner_invalido(owner):
    with pytest.raises(ValueError):
        _validate_owner(owner)


def test_pgvector_serializa_384_dimensoes(monkeypatch):
    from app.services import postgres_vector_service as service
    monkeypatch.setattr(service.settings, "EMBEDDING_DIMENSIONS", 384)
    vector = _vector_literal([0.5] * 384)
    assert vector.startswith("[0.5,0.5,")
    assert vector.endswith("]")
    assert len(vector[1:-1].split(",")) == 384


@pytest.mark.parametrize("vector", [[0.1], [math.nan] * 384, [math.inf] * 384])
def test_pgvector_rejeita_dimensao_ou_valores_invalidos(vector, monkeypatch):
    from app.services import postgres_vector_service as service
    monkeypatch.setattr(service.settings, "EMBEDDING_DIMENSIONS", 384)
    with pytest.raises(ValueError):
        _vector_literal(vector)
