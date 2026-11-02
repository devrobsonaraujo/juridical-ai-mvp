import os
import tempfile
# Tenta a importação padrão e lida com variações de versão do moviepy
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    try:
        from moviepy import VideoFileClip
    except ImportError:
        # Fallback caso a estrutura mude na versão instalada
        from moviepy.video.io.VideoFileClip import VideoFileClip

def extract_audio_from_video(video_file_path: str) -> str:
    """
    Extrai a faixa de áudio de um arquivo de vídeo e salva como MP3 temporário.
    Compatível com moviepy v1.x e v2.x+.
    Retorna o caminho do arquivo de áudio gerado.
    """
    audio_output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    
    try:
        video_clip = VideoFileClip(video_file_path)
        if video_clip.audio is None:
            raise ValueError("O arquivo de vídeo fornecido não possui faixa de áudio.")
        
        # Extrai o áudio com qualidade otimizada para transcrição no Whisper
        video_clip.audio.write_audiofile(
            audio_output_path, 
            bitrate='64k',
            logger=None
        )
        video_clip.close()
        return audio_output_path
    except Exception as e:
        if os.path.exists(audio_output_path):
            os.remove(audio_output_path)
        raise RuntimeError(f"Erro ao extrair áudio do vídeo: {str(e)}")