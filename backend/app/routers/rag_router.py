
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from pydantic import BaseModel, Field

from app.security import CurrentUser, get_current_user
from app.services.rag_service import query_rag_engine


router = APIRouter(
    prefix="/api/v1/rag",
    tags=["Busca Jurídica RAG"],
)


class QueryRequest(BaseModel):
    question: str = Field(
        min_length=1,
    )

    k: int = Field(
        default=4,
        ge=1,
        le=20,
    )

    audio_filter: Optional[str] = None


@router.post("/query")
async def query_audio_knowledge_base(
    payload: QueryRequest,
    current_user: CurrentUser = Depends(
        get_current_user
    ),
):
    """
    Consulta a base jurídica do advogado autenticado.

    O usuário não pode definir o proprietário
    pelo corpo da requisição.
    """
    if not payload.question.strip():
        raise HTTPException(
            status_code=400,
            detail=(
                "A pergunta não pode estar vazia."
            ),
        )

    try:
        result = query_rag_engine(
            question=payload.question,
            k=payload.k,
            audio_filter=payload.audio_filter,
            owner_user_id=current_user.id,
        )

        return {
            "question": payload.question,
            "answer": result["answer"],
            "sources": result["sources"],
        }

    except HTTPException:
        raise

    except Exception as exc:
        print(
            "Erro na consulta RAG "
            f"do usuário {current_user.id}: "
            f"{type(exc).__name__}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Erro ao processar a busca RAG."
            ),
        ) from exc
