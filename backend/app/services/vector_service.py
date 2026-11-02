from chromadb import PersistentClient
from app.config import settings

# Inicialização do Banco Vetorial ChromaDB com Persistência em Disco
db_client = PersistentClient(path="./chroma_db")
collection = db_client.get_or_create_collection(name="juridical_audio_index")

def chunk_segments(segments: list, max_words: int = 150, overlap_words: int = 30) -> list:
    """
    Agrupa segmentos breves do Whisper em janelas de contexto maiores (Sliding Window),
    preservando com exatidão o timestamp inicial (start) e final (end) do bloco.
    Evita perda de contexto probatório em diálogos de audiências.
    """
    chunks = []
    current_chunk_words = []
    current_start = None
    current_end = None

    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        words = text.split()
        if current_start is None:
            current_start = float(seg.get("start", 0.0))

        current_end = float(seg.get("end", 0.0))
        current_chunk_words.extend(words)

        # Se atingir o limite de palavras por janela, consolida o chunk
        if len(current_chunk_words) >= max_words:
            chunk_text = " ".join(current_chunk_words)
            chunks.append({
                "text": chunk_text,
                "start": current_start,
                "end": current_end
            })
            
            # Aplica sobreposição (overlap) para manter a continuidade semântica
            overlap_text = current_chunk_words[-overlap_words:] if len(current_chunk_words) > overlap_words else []
            current_chunk_words = overlap_text
            current_start = current_end

    # Adiciona o último bloco remanescente, se existir
    if current_chunk_words:
        chunks.append({
            "text": " ".join(current_chunk_words),
            "start": current_start,
            "end": current_end
        })

    return chunks

def index_transcript_segments(audio_filename: str, segments: list) -> dict:
    """
    Processa os segmentos do Whisper via janelas deslizantes e indexa os chunks no ChromaDB.
    """
    # Realiza o chunking contextualizado
    contextual_chunks = chunk_segments(segments, max_words=120, overlap_words=25)

    documents = []
    metadatas = []
    ids = []

    for idx, chunk in enumerate(contextual_chunks):
        documents.append(chunk["text"])
        metadatas.append({
            "audio_filename": audio_filename,
            "start": float(chunk["start"]),
            "end": float(chunk["end"])
        })
        ids.append(f"{audio_filename}_chunk_{idx}")

    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    return {
        "status": "indexado",
        "chunks_count": len(documents)
    }

def search_audio_context(query: str, n_results: int = 6, audio_filter: str = None) -> list:
    """
    Busca semântica no ChromaDB filtrada por arquivo (opcional).
    Retorna os blocos vetoriais mais relevantes com seus timestamps.
    """
    where_clause = None
    if audio_filter and audio_filter not in ["Todos os Áudios", "Todas as Mídias"]:
        where_clause = {"audio_filename": audio_filter}

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_clause
    )

    formatted_results = []
    if results and "documents" in results and results["documents"]:
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        for doc, meta in zip(docs, metas):
            formatted_results.append({
                "text": doc,
                "start": meta.get("start", 0.0),
                "end": meta.get("end", 0.0),
                "audio_filename": meta.get("audio_filename", "Mídia")
            })

    return formatted_results

def get_indexed_audio_history() -> list:
    """
    Retorna a lista de arquivos já indexados na base vetorial e o total de blocos por arquivo.
    """
    try:
        all_data = collection.get(include=["metadatas"])
        metadatas = all_data.get("metadatas", [])
        
        file_counts = {}
        for meta in metadatas:
            filename = meta.get("audio_filename")
            if filename:
                file_counts[filename] = file_counts.get(filename, 0) + 1

        history = [{"filename": fname, "chunks_count": count} for fname, count in file_counts.items()]
        return history
    except Exception:
        return []