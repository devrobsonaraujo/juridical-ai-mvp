from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.rag_service import query_rag_engine

router = APIRouter(prefix="/api/v1/rag", tags=["Busca Jurídica RAG"])

class QueryRequest(BaseModel):
    question: str
    k: int = 4  # Quantidade de trechos relevantes a recuperar
    audio_filter: Optional[str] = None  # Permite filtrar a busca por uma mídia específica

@router.post("/query")
async def query_audio_knowledge_base(payload: QueryRequest):
    """
    Recebe uma pergunta jurídica sobre as audiências indexadas e retorna
    a resposta fundamentada com os timestamps exatos das citações via RAG analítico.
    """
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="A pergunta não pode estar vazia.")

    try:
        # Chama o serviço especializado em RAG analítico jurídico (rag_service.py)
        result = query_rag_engine(
            question=payload.question, 
            k=payload.k, 
            audio_filter=payload.audio_filter
        )
        
        return {
            "question": payload.question,
            "answer": result["answer"],
            "sources": result["sources"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a busca RAG: {str(e)}")