
from unittest.mock import MagicMock, patch

import pytest

from app.services.embedding_service import (
    EmbeddingService,
    get_embedding_service,
)
from app.services.embedding_provider import EmbeddingProvider


class FakeVectors:
    def __init__(self, vectors):
        self.vectors = vectors

    def tolist(self):
        return self.vectors


def make_vector(value=0.1):
    return [value] * 384


def test_embedding_service_implements_contract():
    service = EmbeddingService()
    assert isinstance(service, EmbeddingProvider)


def test_empty_documents_do_not_load_model():
    service = EmbeddingService()

    with patch.object(
        EmbeddingService,
        "_load_model",
    ) as loader:
        result = service.embed_documents([])

    assert result == []
    loader.assert_not_called()


def test_documents_are_processed_in_batches():
    model = MagicMock()

    model.encode.side_effect = [
        FakeVectors([
            make_vector(0.1),
            make_vector(0.2),
        ]),
        FakeVectors([
            make_vector(0.3),
        ]),
    ]

    service = EmbeddingService(batch_size=2)

    with patch.object(
        EmbeddingService,
        "_load_model",
        return_value=model,
    ):
        result = service.embed_documents([
            "Primeiro depoimento",
            "Segundo depoimento",
            "Terceiro depoimento",
        ])

    assert len(result) == 3
    assert model.encode.call_count == 2

    first_batch = model.encode.call_args_list[0].args[0]
    second_batch = model.encode.call_args_list[1].args[0]

    assert first_batch == [
        "passage: Primeiro depoimento",
        "passage: Segundo depoimento",
    ]

    assert second_batch == [
        "passage: Terceiro depoimento",
    ]


def test_query_uses_correct_prefix():
    model = MagicMock()
    model.encode.return_value = FakeVectors([
        make_vector(),
    ])

    service = EmbeddingService()

    with patch.object(
        EmbeddingService,
        "_load_model",
        return_value=model,
    ):
        result = service.embed_query(
            "Qual foi o horário da audiência?"
        )

    assert len(result) == 384

    prepared = model.encode.call_args.args[0]

    assert prepared == [
        "query: Qual foi o horário da audiência?"
    ]


def test_rejects_invalid_dimension():
    model = MagicMock()
    model.encode.return_value = FakeVectors([
        [0.1] * 100,
    ])

    service = EmbeddingService()

    with patch.object(
        EmbeddingService,
        "_load_model",
        return_value=model,
    ):
        with pytest.raises(
            ValueError,
            match="Dimensão inesperada",
        ):
            service.embed_query("Pergunta fictícia")


def test_rejects_non_finite_vectors():
    model = MagicMock()
    model.encode.return_value = FakeVectors([
        [float("nan")] * 384,
    ])

    service = EmbeddingService()

    with patch.object(
        EmbeddingService,
        "_load_model",
        return_value=model,
    ):
        with pytest.raises(
            ValueError,
            match="valores inválidos",
        ):
            service.embed_query("Pergunta fictícia")


def test_rejects_invalid_batch_size():
    with pytest.raises(
        ValueError,
        match="positivo",
    ):
        EmbeddingService(batch_size=0)


def test_factory_returns_cached_provider():
    get_embedding_service.cache_clear()

    try:
        first = get_embedding_service()
        second = get_embedding_service()

        assert first is second
        assert isinstance(first, EmbeddingService)
    finally:
        get_embedding_service.cache_clear()


def test_factory_rejects_unknown_provider(monkeypatch):
    from app.config import settings

    get_embedding_service.cache_clear()

    monkeypatch.setattr(
        settings,
        "EMBEDDING_PROVIDER",
        "unsupported",
    )

    try:
        with pytest.raises(
            ValueError,
            match="não suportado",
        ):
            get_embedding_service()
    finally:
        get_embedding_service.cache_clear()
