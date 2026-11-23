
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def extract_audio_from_video(video_file_path: str) -> str:
    """
    Extrai o áudio de um vídeo utilizando FFmpeg.

    O áudio é convertido para MP3 mono, 16 kHz,
    com bitrate de 64 kbps.

    Retorna o caminho do arquivo temporário gerado.

    O chamador é responsável por remover esse arquivo
    após a transcrição.
    """

    video_path = Path(video_file_path)

    if not video_path.is_file():
        raise FileNotFoundError(
            "O arquivo de vídeo não foi encontrado."
        )

    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "FFmpeg não encontrado no PATH."
        )

    fd, audio_output_path = tempfile.mkstemp(
        suffix=".mp3"
    )
    os.close(fd)

    try:
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-i", str(video_path),
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-b:a", "64k",
            audio_output_path,
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "FFmpeg não conseguiu extrair o áudio."
            )

        if (
            not os.path.isfile(audio_output_path)
            or os.path.getsize(audio_output_path) == 0
        ):
            raise RuntimeError(
                "A extração gerou um arquivo de áudio vazio."
            )

        return audio_output_path

    except Exception:
        if os.path.isfile(audio_output_path):
            os.remove(audio_output_path)

        raise
