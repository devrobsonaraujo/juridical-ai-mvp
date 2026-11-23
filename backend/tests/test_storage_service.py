
from unittest.mock import MagicMock, patch

import pytest

from app.services import storage_service


OWNER_ID = "11111111-1111-4111-8111-111111111111"


@pytest.mark.parametrize(
    "backend",
    ["chroma", "postgres"],
)
def test_aceita_backends_suportados(
    monkeypatch,
    backend,
):
    monkeypatch.setattr(
        storage_service.settings,
        "STORAGE_BACKEND",
        backend,
    )

    assert storage_service.get_storage_backend() == backend


def test_rejeita_backend_desconhecido(monkeypatch):
    monkeypatch.setattr(
        storage_service.settings,
        "STORAGE_BACKEND",
        "desconhecido",
    )

    with pytest.raises(
        ValueError,
        match="STORAGE_BACKEND inválido",
    ):
        storage_service.get_storage_backend()


def test_indexacao_encaminha_proprietario():
    fake_storage = MagicMock()
    fake_storage.index_transcript_segments.return_value = {
        "status": "indexado",
        "chunks_count": 1,
    }

    segments = [
        {
            "text": "Depoimento fictício.",
            "start": 0.0,
            "end": 5.0,
        }
    ]

    with patch.object(
        storage_service,
        "get_storage_module",
        return_value=fake_storage,
    ):
        result = storage_service.index_transcript_segments(
            audio_filename="teste.mp3",
            segments=segments,
            owner_user_id=OWNER_ID,
        )

    assert result["status"] == "indexado"

    fake_storage.index_transcript_segments.assert_called_once_with(
        audio_filename="teste.mp3",
        segments=segments,
        owner_user_id=OWNER_ID,
    )


def test_historico_encaminha_proprietario():
    fake_storage = MagicMock()
    fake_storage.get_indexed_audio_history.return_value = []

    with patch.object(
        storage_service,
        "get_storage_module",
        return_value=fake_storage,
    ):
        result = storage_service.get_indexed_audio_history(
            owner_user_id=OWNER_ID,
        )

    assert result == []

    fake_storage.get_indexed_audio_history.assert_called_once_with(
        owner_user_id=OWNER_ID,
    )


def test_busca_encaminha_proprietario_e_filtro():
    fake_storage = MagicMock()
    fake_storage.search_audio_context.return_value = []

    with patch.object(
        storage_service,
        "get_storage_module",
        return_value=fake_storage,
    ):
        result = storage_service.search_audio_context(
            query="O que a testemunha disse?",
            n_results=4,
            audio_filter="teste.mp3",
            owner_user_id=OWNER_ID,
        )

    assert result == []

    fake_storage.search_audio_context.assert_called_once_with(
        query="O que a testemunha disse?",
        n_results=4,
        audio_filter="teste.mp3",
        owner_user_id=OWNER_ID,
    )


@pytest.mark.parametrize(
    "operation",
    ["index", "history", "search"],
)
def test_rejeita_operacoes_sem_proprietario(operation):
    with patch.object(
        storage_service,
        "get_storage_module",
    ) as mock_storage:
        with pytest.raises(ValueError):
            if operation == "index":
                storage_service.index_transcript_segments(
                    audio_filename="teste.mp3",
                    segments=[],
                    owner_user_id="",
                )

            elif operation == "history":
                storage_service.get_indexed_audio_history(
                    owner_user_id="",
                )

            else:
                storage_service.search_audio_context(
                    query="Teste",
                    owner_user_id=None,
                )

        mock_storage.assert_not_called()
