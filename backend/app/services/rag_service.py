
from app.ai.factory import get_ai_provider
from app.services.vector_service import search_audio_context


def query_rag_engine(
    question: str,
    k: int = 6,
    audio_filter: str | None = None
) -> dict:
    """
    Serviço analítico de RAG focado em apuração probatória jurídica.

    Responsabilidades:
    1. Recuperar trechos relevantes do ChromaDB.
    2. Construir o contexto com timestamps.
    3. Preparar os prompts jurídicos.
    4. Delegar a geração da resposta ao provedor de IA.
    5. Retornar a resposta e suas fontes.
    """

    # 1. Recupera os trechos contextualizados
    context_segments = search_audio_context(
        query=question,
        n_results=k,
        audio_filter=audio_filter
    )

    # 2. Formata o contexto preservando timestamps [MM:SS]
    context_chunks = []

    for segment in context_segments:
        start_sec = int(segment["start"])
        minutes, seconds = divmod(start_sec, 60)

        context_chunks.append(
            f"[{minutes:02d}:{seconds:02d} - "
            f"{segment['audio_filename']}]: {segment['text']}"
        )

    context_str = "\n\n".join(context_chunks)

    # 3. Prompt jurídico original - preservado
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

    # 4. Geração de resposta pelo provedor configurado
    provider = get_ai_provider()

    answer = provider.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )

    # 5. Retorna o contrato esperado pelo frontend
    return {
        "answer": answer,
        "sources": context_segments
    }
