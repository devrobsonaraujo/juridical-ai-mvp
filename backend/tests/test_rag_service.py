
from unittest.mock import MagicMock, patch

import pytest

from app.services.rag_service import query_rag_engine


ADVOGADO_A = "11111111-1111-4111-8111-111111111111"


def criar_trechos_simulados():
    return [
        {
            "text": "A testemunha afirmou que chegou às 10 horas.",
            "start": 65.0,
            "end": 78.0,
            "audio_filename": "audiencia_teste.mp3",
        },
        {
            "text": "Posteriormente, declarou que não recordava o horário.",
            "start": 125.0,
            "end": 140.0,
            "audio_filename": "audiencia_teste.mp3",
        },
    ]


def test_rag_retorna_resposta_e_fontes():
    trechos = criar_trechos_simulados()

    with (
        patch(
            "app.services.rag_service.search_audio_context",
            return_value=trechos,
        ) as mock_search,
        patch(
            "app.services.rag_service.get_ai_provider"
        ) as mock_factory,
    ):
        mock_factory.return_value.generate.return_value = (
            "A testemunha apresentou declarações "
            "sobre o horário. [01:05] [02:05]"
        )

        result = query_rag_engine(
            question="O que a testemunha declarou?",
            owner_user_id=ADVOGADO_A,
        )

        assert result["answer"]
        assert result["sources"] == trechos

        mock_search.assert_called_once_with(
            query="O que a testemunha declarou?",
            n_results=6,
            audio_filter=None,
            owner_user_id=ADVOGADO_A,
        )

        mock_factory.return_value.generate.assert_called_once()


def test_rag_preserva_timestamps_no_prompt():
    trechos = criar_trechos_simulados()

    with (
        patch(
            "app.services.rag_service.search_audio_context",
            return_value=trechos,
        ),
        patch(
            "app.services.rag_service.get_ai_provider"
        ) as mock_factory,
    ):
        mock_factory.return_value.generate.return_value = (
            "Resposta simulada"
        )

        query_rag_engine(
            question="Quais foram as declarações?",
            owner_user_id=ADVOGADO_A,
        )

        mock_factory.return_value.generate.assert_called_once()

        args = (
            mock_factory.return_value.generate.call_args
        )

        user_prompt = args.kwargs["user_prompt"]

        assert "[01:05 - audiencia_teste.mp3]" in user_prompt
        assert "[02:05 - audiencia_teste.mp3]" in user_prompt

        assert "Quais foram as declarações?" in user_prompt


def test_rag_preserva_fontes_originais():
    trechos = criar_trechos_simulados()

    with (
        patch(
            "app.services.rag_service.search_audio_context",
            return_value=trechos,
        ),
        patch(
            "app.services.rag_service.get_ai_provider"
        ) as mock_factory,
    ):
        mock_factory.return_value.generate.return_value = (
            "Resposta simulada"
        )

        result = query_rag_engine(
            question="Analise o depoimento.",
            owner_user_id=ADVOGADO_A,
        )

        assert result["sources"] == trechos

        assert result["sources"][0]["start"] == 65.0
        assert result["sources"][0]["end"] == 78.0

        assert (
            result["sources"][0]["audio_filename"]
            == "audiencia_teste.mp3"
        )


def test_rag_sem_trechos_recuperados():
    """
    Quando não existem fontes, o RAG não deve
    chamar o modelo de IA.
    """
    with (
        patch(
            "app.services.rag_service.search_audio_context",
            return_value=[],
        ) as mock_search,
        patch(
            "app.services.rag_service.get_ai_provider"
        ) as mock_factory,
    ):
        result = query_rag_engine(
            question="Qual foi a decisão judicial?",
            owner_user_id=ADVOGADO_A,
        )

        assert result == {
            "answer": (
                "A informação não consta nos trechos "
                "recuperados desta audiência."
            ),
            "sources": [],
        }

        mock_search.assert_called_once()
        mock_factory.assert_not_called()


def test_rag_rejeita_consulta_sem_proprietario():
    """
    Uma consulta sem advogado identificado
    deve ser bloqueada antes da busca vetorial.
    """
    with (
        patch(
            "app.services.rag_service.search_audio_context"
        ) as mock_search,
        patch(
            "app.services.rag_service.get_ai_provider"
        ) as mock_factory,
    ):
        with pytest.raises(
            ValueError,
            match="proprietário é obrigatório",
        ):
            query_rag_engine(
                question="Analise o depoimento."
            )

        mock_search.assert_not_called()
        mock_factory.assert_not_called()


def test_rag_encaminha_filtro_e_proprietario():
    """
    O filtro de mídia não pode substituir
    o filtro obrigatório de proprietário.
    """
    with (
        patch(
            "app.services.rag_service.search_audio_context",
            return_value=[],
        ) as mock_search,
        patch(
            "app.services.rag_service.get_ai_provider"
        ) as mock_factory,
    ):
        query_rag_engine(
            question="O que aconteceu?",
            k=4,
            audio_filter="audiencia_teste.mp3",
            owner_user_id=ADVOGADO_A,
        )

        mock_search.assert_called_once_with(
            query="O que aconteceu?",
            n_results=4,
            audio_filter="audiencia_teste.mp3",
            owner_user_id=ADVOGADO_A,
        )

        mock_factory.assert_not_called()
