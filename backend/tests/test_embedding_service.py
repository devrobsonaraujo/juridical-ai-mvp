
from unittest.mock import MagicMock, patch

import pytest

from app.services.embedding_service import EmbeddingService


class FakeVectors:
    def __init__(self, vectors):
        self.vectors = vectors

    def tolist(self):
        return self.vectors


def make_vector():
    return [0.01] * 384


def test_embedding_documentos_usa_prefixo_passage():
    service = EmbeddingService()

    model = MagicMock()
    model.encode.return_value = FakeVectors(
        [make_vector()]
    )

    with patch.object(
        EmbeddingService,
        "_load_model",
        return_value=model,
    ):
        result = service.embed_documents(
            ["A testemunha prestou depoimento."]
        )

    assert len(result) == 1
    assert len(result[0]) == 384

    args = model.encode.call_args.args[0]

    assert args == [
        "passage: A testemunha prestou depoimento."
    ]


def test_embedding_pergunta_usa_prefixo_query():
    service = EmbeddingService()

    model = MagicMock()
    model.encode.return_value = FakeVectors(
        [make_vector()]
    )

    with patch.object(
        EmbeddingService,
        "_load_model",
        return_value=model,
    ):
        result = service.embed_query(
            "Qual foi o depoimento?"
        )

    assert len(result) == 384

    args = model.encode.call_args.args[0]

    assert args == [
        "query: Qual foi o depoimento?"
    ]


def test_embedding_rejeita_texto_vazio():
    service = EmbeddingService()

    with pytest.raises(ValueError):
        service.embed_documents([""])


def test_embedding_rejeita_dimensao_incorreta():
    service = EmbeddingService()

    model = MagicMock()
    model.encode.return_value = FakeVectors(
        [[0.1] * 10]
    )

    with patch.object(
        EmbeddingService,
        "_load_model",
        return_value=model,
    ):
        with pytest.raises(
            ValueError,
            match="Dimensão inesperada",
        ):
            service.embed_documents(
                ["Depoimento fictício."]
            )
