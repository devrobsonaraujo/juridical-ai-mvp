import os
import math
from pydub import AudioSegment
from openai import OpenAI
from app.config import settings

# Inicialização do cliente com a Groq
client = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

MAX_FILE_SIZE_MB = 24  # Margem de segurança abaixo de 25MB

def get_file_size_mb(file_path: str) -> float:
    """Retorna o tamanho do arquivo em MB."""
    return os.path.getsize(file_path) / (1024 * 1024)

def split_audio_file(file_path: str, chunk_length_minutes: int = 10) -> list[dict]:
    """
    Divide um arquivo de áudio pesado em partes menores.
    Retorna uma lista de dicionários contendo o caminho do chunk e o tempo inicial de deslocamento (offset).
    """
    audio = AudioSegment.from_file(file_path)
    chunk_length_ms = chunk_length_minutes * 60 * 1000  
    total_chunks = math.ceil(len(audio) / chunk_length_ms)
    
    chunks_info = []
    base_name, ext = os.path.splitext(file_path)

    for i in range(total_chunks):
        start_ms = i * chunk_length_ms
        end_ms = min((i + 1) * chunk_length_ms, len(audio))
        
        chunk_audio = audio[start_ms:end_ms]
        chunk_filename = f"{base_name}_part_{i}{ext}"
        
        chunk_audio.export(chunk_filename, format=ext.replace(".", ""))
        offset_seconds = start_ms / 1000.0
        
        chunks_info.append({
            "path": chunk_filename,
            "offset": offset_seconds
        })

    return chunks_info

def transcribe_audio_file(file_path: str) -> dict:
    """
    Processa arquivos de áudio de qualquer tamanho utilizando o objeto correto do Whisper.
    """
    file_size = get_file_size_mb(file_path)
    unified_segments = []
    full_text_parts = []

    if file_size <= MAX_FILE_SIZE_MB:
        chunks_to_process = [{"path": file_path, "offset": 0.0}]
    else:
        print(f"Áudio grande detectado ({file_size:.2f}MB). Iniciando fatiamento...")
        chunks_to_process = split_audio_file(file_path, chunk_length_minutes=10)

    for chunk in chunks_to_process:
        chunk_path = chunk["path"]
        time_offset = chunk["offset"]

        with open(chunk_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio_file,
                response_format="verbose_json",
                language="pt"
            )

            # Extrai os segmentos acessando como atributos do objeto
            segments = getattr(response, "segments", [])
            for seg in segments:
                # O objeto TranscriptionSegment usa atributos (seg.start, seg.end, seg.text)
                seg_start = getattr(seg, "start", 0.0)
                seg_end = getattr(seg, "end", 0.0)
                seg_text = getattr(seg, "text", "").strip()

                real_start = seg_start + time_offset
                real_end = seg_end + time_offset

                unified_segments.append({
                    "start": real_start,
                    "end": real_end,
                    "text": seg_text
                })
                full_text_parts.append(seg_text)

        # Remove o chunk temporário se foi criado pelo fatiamento
        if chunk_path != file_path and os.path.exists(chunk_path):
            os.remove(chunk_path)

    return {
        "full_text": " ".join(full_text_parts),
        "segments": unified_segments
    }