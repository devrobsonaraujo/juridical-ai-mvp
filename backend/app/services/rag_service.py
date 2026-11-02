import os
from groq import Groq
from app.config import settings
from app.services.vector_service import search_audio_context

def query_rag_engine(question: str, k: int = 6, audio_filter: str = None) -> dict:
    """
    Serviço analítico de RAG focado em apuração probatória jurídica.
    """
    client = Groq(api_key=settings.GROQ_API_KEY)

    # 1. Busca os blocos contextualizados via janela deslizante do vector_service
    context_segments = search_audio_context(query=question, n_results=k, audio_filter=audio_filter)

    # 2. Formata o contexto preservando relógio temporal [MM:SS]
    context_chunks = []
    for s in context_segments:
        start_sec = int(s["start"])
        m, sec = divmod(start_sec, 60)
        context_chunks.append(f"[{m:02d}:{sec:02d} - {s['audio_filename']}]: {s['text']}")

    context_str = "\n\n".join(context_chunks)

    # 3. Prompt do Sistema de Alta Rigidez Probatória
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

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",  # Ou "llama-3.3-70b-versatile"
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        max_tokens=1500
    )

    return {
        "answer": completion.choices[0].message.content,
        "sources": context_segments
    }