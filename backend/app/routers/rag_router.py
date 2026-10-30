from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.vector_service import query_rag_audio

router = APIRouter(prefix="/api/v1/rag", tags=["Busca Jurídica RAG"])

class QueryRequest(BaseModel):
    question: str
    k: int = 4  # Quantidade de trechos relevantes a recuperar

@router.post("/query")
async def query_audio_knowledge_base(payload: QueryRequest):
    """
    Recebe uma pergunta jurídica sobre as audiências indexadas e retorna
    a resposta fundamentada com os timestamps exatos das citações.
    """
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="A pergunta não pode estar vazia.")

    try:
        result = query_rag_audio(question=payload.question, k=payload.k)
        return {
            "question": payload.question,
            "answer": result["answer"],
            "sources": result["sources"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a busca RAG: {str(e)}")