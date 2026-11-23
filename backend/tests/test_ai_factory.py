
import pytest
from unittest.mock import patch

from app.ai.factory import get_ai_provider
from app.ai.providers.groq_provider import GroqProvider


def test_factory_retorna_groq_provider(monkeypatch):
    """
    Verifica se a Factory seleciona a Groq.
    Não faz chamadas externas.
    """

    monkeypatch.setattr(
        "app.ai.factory.settings.AI_PROVIDER",
        "groq",
    )

    monkeypatch.setattr(
        "app.ai.factory.settings.AI_MODEL",
        "modelo-de-teste",
    )

    monkeypatch.setattr(
        "app.ai.factory.settings.GROQ_API_KEY",
        "chave-ficticia",
    )

    with patch(
        "app.ai.providers.groq_provider.Groq"
    ) as mock_groq:
        provider = get_ai_provider()

    assert isinstance(provider, GroqProvider)
    assert provider.model == "modelo-de-teste"

    mock_groq.assert_called_once_with(
        api_key="chave-ficticia"
    )


def test_factory_aceita_provedor_maiusculo(monkeypatch):
    """
    Verifica se espaços e letras maiúsculas
    são normalizados.
    """

    monkeypatch.setattr(
        "app.ai.factory.settings.AI_PROVIDER",
        " GROQ ",
    )

    with patch(
        "app.ai.providers.groq_provider.Groq"
    ):
        provider = get_ai_provider()

    assert isinstance(provider, GroqProvider)


def test_factory_rejeita_provedor_desconhecido(
    monkeypatch,
):
    """
    Impede a utilização de provedores
    que ainda não foram implementados.
    """

    monkeypatch.setattr(
        "app.ai.factory.settings.AI_PROVIDER",
        "provedor-inexistente",
    )

    with pytest.raises(
        ValueError,
        match="Provedor de IA não suportado",
    ):
        get_ai_provider()
