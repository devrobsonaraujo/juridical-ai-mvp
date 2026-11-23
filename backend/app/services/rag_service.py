
from app.ai.factory import get_ai_provider
from app.services.storage_service import search_audio_context


def query_rag_engine(
    question: str,
    k: int = 6,
    audio_filter: str | None = None,
    owner_user_id: str | None = None,
) -> dict:
    """
    Serviço analítico de RAG para apuração probatória.

    Todas as buscas são limitadas ao advogado
    autenticado.

    O armazenamento é selecionado pelo storage_service.
    """
    if not owner_user_id:
        raise ValueError(
            "O proprietário é obrigatório para consultas RAG."
        )

    # 1. Recuperação com isolamento obrigatório
    context_segments = search_audio_context(
        query=question,
        n_results=k,
        audio_filter=audio_filter,
        owner_user_id=owner_user_id,
    )

    # Não chamar o modelo quando não houver fontes.
    if not context_segments:
        return {
            "answer": (
                "A informação não consta nos trechos "
                "recuperados desta audiência."
            ),
            "sources": [],
        }

    # 2. Contexto com timestamps
    context_chunks = []

    for segment in context_segments:
        start_sec = int(segment["start"])
        minutes, seconds = divmod(
            start_sec,
            60,
        )

        context_chunks.append(
            f"[{minutes:02d}:{seconds:02d} - "
            f"{segment['audio_filename']}]: "
            f"{segment['text']}"
        )

    context_str = "\n\n".join(context_chunks)

    # 3. Prompt jurídico original preservado
    system_prompt = """Você é um Assessor Jurídico Sênior especialista na análise de depoimentos e audiências judiciais.
Sua função é responder pontualmente à indagação formulada usando EXCLUSIVAMENTE os fatos relatados nos trechos recuperados.

REGRAS OBRIGATÓRIAS:
1. Jamais deduza, invente ou assuma informações não contidas explicitamente nos trechos.
2. Identifique respostas evasivas, contradições ou declarações de esquecimento ("não recordo").
3. Vincule suas conclusões aos timestamps [MM:SS].
4. Se a informação não for encontrada nos trechos recuperados, responda com clareza: "A informação não consta nos trechos recuperados desta audiência."
"""

    user_prompt = f"""TRECHOS DA AUDIÊNCIA DEGRAVADA:
{context_str}

PERGUNTA DO ADVOGADO/MAGISTRADO:
{question}

Responda de forma direta e técnica:"""

    # 4. Geração pelo provedor configurado
    provider = get_ai_provider()

    answer = provider.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    # 5. Contrato preservado para o React
    return {
        "answer": answer,
        "sources": context_segments,
    }
