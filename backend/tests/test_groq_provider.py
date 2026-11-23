
from unittest.mock import MagicMock, patch

from app.ai.providers.groq_provider import GroqProvider


def test_groq_provider_gera_resposta():
    """
    Simula uma resposta da Groq sem
    realizar requisições externas.
    """

    resposta_simulada = MagicMock()
    resposta_simulada.choices = [
        MagicMock(
            message=MagicMock(
                content="Resposta jurídica simulada."
            )
        )
    ]

    with patch(
        "app.ai.providers.groq_provider.Groq"
    ) as mock_groq:
        mock_client = mock_groq.return_value

        mock_client.chat.completions.create.return_value = (
            resposta_simulada
        )

        provider = GroqProvider(
            api_key="chave-ficticia",
            model="modelo-de-teste",
        )

        answer = provider.generate(
            system_prompt="Você é um assessor jurídico.",
            user_prompt="Resuma a audiência.",
        )

        assert answer == "Resposta jurídica simulada."

        mock_client.chat.completions.create.assert_called_once_with(
            model="modelo-de-teste",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assessor jurídico.",
                },
                {
                    "role": "user",
                    "content": "Resuma a audiência.",
                },
            ],
            temperature=0.1,
            max_tokens=1500,
        )


def test_groq_provider_retorna_string_vazia():
    """
    Verifica o comportamento quando o
    modelo não retorna conteúdo textual.
    """

    resposta_simulada = MagicMock()
    resposta_simulada.choices = [
        MagicMock(
            message=MagicMock(content=None)
        )
    ]

    with patch(
        "app.ai.providers.groq_provider.Groq"
    ) as mock_groq:
        mock_client = mock_groq.return_value

        mock_client.chat.completions.create.return_value = (
            resposta_simulada
        )

        provider = GroqProvider(
            api_key="chave-ficticia",
            model="modelo-de-teste",
        )

        answer = provider.generate(
            system_prompt="Sistema",
            user_prompt="Pergunta",
        )

        assert answer == ""
