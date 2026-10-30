import os
from pydub import AudioSegment

def split_audio_if_needed(file_path: str, max_size_mb: int = 24) -> list[str]:
    """
    Verifica o tamanho do arquivo de áudio. Se for maior que max_size_mb (padrão 24MB),
    divide o áudio em partes menores e retorna uma lista com os caminhos dos arquivos gerados.
    Caso contrário, retorna o caminho do arquivo original em uma lista.
    """
    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)

    print(f"Tamanho do arquivo de áudio: {file_size_mb:.2f} MB")

    if file_size_mb <= max_size_mb:
        return [file_path]

    print(f"Arquivo maior que {max_size_mb}MB. Iniciando fatiamento com pydub...")
    
    # Carrega o áudio (suporta mp3, wav, m4a, etc. se o ffmpeg estiver instalado)
    audio = AudioSegment.from_file(file_path)
    
    # Define o tamanho de cada chunk em milissegundos (ex: 10 minutos por chunk = 600.000 ms)
    chunk_length_ms = 10 * 60 * 1000 
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

    base_dir = os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    chunk_paths = []
    for index, chunk in enumerate(chunks):
        chunk_name = os.path.join(base_dir, f"{base_name}_part_{index + 1}.mp3")
        # Exporta cada pedaço mantendo uma qualidade otimizada para voz (16kbps mono ou similar)
        chunk.export(chunk_name, format="mp3", bitrate="64k")
        chunk_paths.append(chunk_name)
        print(f"Criado chunk: {chunk_name}")

    return chunk_paths