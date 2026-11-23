
import os
import shutil
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from app.config import settings
from app.security import CurrentUser, get_current_user
from app.services.media_service import extract_audio_from_video
from app.services.transcription_service import transcribe_audio_file
from app.services.storage_service import (
    get_indexed_audio_history,
    index_transcript_segments,
)


router = APIRouter(
    prefix="/api/v1/audio",
    tags=["Mídia e Transcrição"],
)

ALLOWED_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".mp4",
    ".mpeg",
    ".mpga",
    ".webm",
    ".mkv",
    ".avi",
    ".mov",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".webm",
}


@router.post("/transcribe")
async def transcribe_and_index_audio(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(
        get_current_user
    ),
):
    """
    Transcreve e indexa uma mídia para o advogado
    autenticado, com proprietário obrigatório.

    O armazenamento é selecionado pelo storage_service.
    """
    original_filename = Path(
        (file.filename or "").replace("\\", "/")
    ).name

    file_ext = Path(
        original_filename
    ).suffix.lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Formato de arquivo não suportado. "
                "Extensões permitidas: "
                f"{', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    os.makedirs(
        settings.TEMP_DIR,
        exist_ok=True,
    )

    temp_filename = (
        f"{uuid.uuid4().hex}{file_ext}"
    )

    temp_file_path = os.path.join(
        settings.TEMP_DIR,
        temp_filename,
    )

    audio_path_to_process = temp_file_path

    try:
        with open(
            temp_file_path,
            "wb",
        ) as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        if file_ext in VIDEO_EXTENSIONS:
            audio_path_to_process = (
                extract_audio_from_video(
                    temp_file_path
                )
            )

        transcript_result = transcribe_audio_file(
            audio_path_to_process
        )

        indexing_result = index_transcript_segments(
            audio_filename=original_filename,
            segments=transcript_result["segments"],
            owner_user_id=current_user.id,
        )

        return {
            "filename": original_filename,
            "status": "sucesso",
            "full_text": transcript_result["full_text"],
            "segments_count": len(
                transcript_result["segments"]
            ),
            "indexing": indexing_result,
        }

    except HTTPException:
        raise

    except Exception as exc:
        print(
            "Erro ao processar mídia "
            f"do usuário {current_user.id}: "
            f"{type(exc).__name__}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Erro interno no processamento da mídia."
            ),
        ) from exc

    finally:
        await file.close()

        for path in {
            temp_file_path,
            audio_path_to_process,
        }:
            if os.path.isfile(path):
                os.remove(path)


@router.get("/history")
async def get_indexed_history(
    current_user: CurrentUser = Depends(
        get_current_user
    ),
):
    """
    Retorna somente as mídias do advogado autenticado,
    utilizando o armazenamento configurado.
    """
    try:
        history = get_indexed_audio_history(
            owner_user_id=current_user.id
        )

        return {
            "status": "sucesso",
            "history": history,
        }

    except Exception as exc:
        print(
            "Erro ao consultar histórico "
            f"do usuário {current_user.id}: "
            f"{type(exc).__name__}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível consultar o histórico."
            ),
        ) from exc
