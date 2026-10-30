import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import settings
from app.services.transcription_service import transcribe_audio_file
from app.services.vector_service import index_transcript_segments

router = APIRouter(prefix="/api/v1/audio", tags=["Áudio e Transcrição"])

@router.post("/transcribe")
async def transcribe_and_index_audio(file: UploadFile = File(...)):
    """
    Recebe um arquivo de áudio (mp3, wav, m4a), salva temporariamente,
    realiza a transcrição via Whisper (com suporte a fatiamento se > 24MB)
    e indexa os segmentos no ChromaDB.
    """
    allowed_extensions = [".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Formato de arquivo não suportado. Use um dos seguintes: {allowed_extensions}"
        )

    # Salva o arquivo temporariamente na pasta temp/
    temp_file_path = os.path.join(settings.TEMP_DIR, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"Arquivo recebido e salvo em: {temp_file_path}")

        # 1. Executa a transcrição com preservação de timestamps
        transcript_result = transcribe_audio_file(temp_file_path)

        # 2. Indexa automaticamente os segmentos no banco vetorial (ChromaDB)
        indexing_result = index_transcript_segments(
            audio_filename=file.filename,
            segments=transcript_result["segments"]
        )

        return {
            "filename": file.filename,
            "status": "sucesso",
            "full_text": transcript_result["full_text"],
            "segments_count": len(transcript_result["segments"]),
            "indexing": indexing_result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no processamento do áudio: {str(e)}")
    
    finally:
        # Remove o arquivo temporário original da pasta temp para poupar espaço
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)