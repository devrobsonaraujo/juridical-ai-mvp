
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from openai import OpenAI

from app.config import settings


client = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    timeout=180.0,
    max_retries=2,
)

MAX_FILE_SIZE_MB = 24


def get_file_size_mb(file_path: str) -> float:
    """Retorna o tamanho do arquivo em MiB."""
    return os.path.getsize(file_path) / (1024 * 1024)


def _run_ffmpeg(command: list[str]) -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "FFmpeg não encontrado no PATH."
        )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Falha ao processar áudio com FFmpeg."
        )


def _get_audio_duration(file_path: str) -> float:
    if shutil.which("ffprobe") is None:
        raise RuntimeError(
            "FFprobe não encontrado no PATH."
        )

    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Não foi possível identificar a duração do áudio."
        )

    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(
            "Duração de áudio inválida."
        ) from exc

    if not math.isfinite(duration) or duration <= 0:
        raise RuntimeError(
            "O áudio possui duração inválida."
        )

    return duration


def split_audio_file(
    file_path: str,
    chunk_length_minutes: int = 10,
) -> list[dict]:
    """
    Divide o áudio em arquivos MP3 temporários.

    Não carrega a mídia inteira na memória.

    Retorna:
    [
        {"path": "...", "offset": 0.0},
        {"path": "...", "offset": 600.0},
    ]

    O chamador deve remover os arquivos gerados.
    """
    if chunk_length_minutes < 1:
        raise ValueError(
            "A duração dos chunks deve ser positiva."
        )

    duration = _get_audio_duration(file_path)
    chunk_seconds = chunk_length_minutes * 60
    total_chunks = math.ceil(duration / chunk_seconds)

    chunks_info = []

    try:
        for index in range(total_chunks):
            offset = index * chunk_seconds
            remaining = duration - offset

            if remaining <= 0:
                break

            current_duration = min(
                chunk_seconds,
                remaining,
            )

            fd, chunk_path = tempfile.mkstemp(
                suffix=".mp3"
            )
            os.close(fd)

            chunks_info.append({
                "path": chunk_path,
                "offset": float(offset),
            })

            _run_ffmpeg([
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "error",
                "-y",
                "-ss", str(offset),
                "-i", file_path,
                "-t", str(current_duration),
                "-vn",
                "-ac", "1",
                "-ar", "16000",
                "-b:a", "64k",
                chunk_path,
            ])

            if os.path.getsize(chunk_path) == 0:
                raise RuntimeError(
                    "O FFmpeg gerou um chunk vazio."
                )

            if get_file_size_mb(chunk_path) > MAX_FILE_SIZE_MB:
                raise RuntimeError(
                    "Um chunk ultrapassou o limite "
                    "de tamanho para transcrição."
                )

        return chunks_info

    except Exception:
        for chunk in chunks_info:
            path = chunk["path"]

            if os.path.exists(path):
                os.remove(path)

        raise


def transcribe_audio_file(file_path: str) -> dict:
    """
    Transcreve um áudio usando Groq Whisper.

    Preserva o contrato:
    {
        "full_text": str,
        "segments": [
            {
                "start": float,
                "end": float,
                "text": str,
            }
        ]
    }
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            "Arquivo de áudio não encontrado."
        )

    file_size = get_file_size_mb(file_path)

    if file_size <= MAX_FILE_SIZE_MB:
        chunks_to_process = [{
            "path": file_path,
            "offset": 0.0,
        }]
    else:
        chunks_to_process = split_audio_file(
            file_path,
            chunk_length_minutes=10,
        )

    unified_segments = []
    full_text_parts = []

    try:
        for chunk in chunks_to_process:
            chunk_path = chunk["path"]
            time_offset = chunk["offset"]

            with open(chunk_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=audio_file,
                    response_format="verbose_json",
                    language="pt",
                )

            segments = getattr(
                response,
                "segments",
                None,
            ) or []

            for segment in segments:
                text = (
                    getattr(segment, "text", "") or ""
                ).strip()

                if not text:
                    continue

                start = float(
                    getattr(segment, "start", 0.0)
                ) + time_offset

                end = float(
                    getattr(segment, "end", 0.0)
                ) + time_offset

                unified_segments.append({
                    "start": start,
                    "end": end,
                    "text": text,
                })

                full_text_parts.append(text)

        return {
            "full_text": " ".join(full_text_parts),
            "segments": unified_segments,
        }

    finally:
        for chunk in chunks_to_process:
            chunk_path = chunk["path"]

            if chunk_path == file_path:
                continue

            if os.path.isfile(chunk_path):
                os.remove(chunk_path)
