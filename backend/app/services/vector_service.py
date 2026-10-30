from chromadb import PersistentClient
from openai import OpenAI
from app.config import settings

client = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

db_client = PersistentClient(path="./chroma_db")
collection = db_client.get_or_create_collection(name="juridical_audio_index")

def index_transcription(audio_id: str, segments: list):
    """Indexa os segmentos da transcrição no ChromaDB."""
    documents = []
    metadatas = []
    ids = []
    
    for idx, seg in enumerate(segments):
        doc_text = seg["text"]
        documents.append(doc_text)
        metadatas.append({
            "audio_id": audio_id,
            "start": seg["start"],
            "end": seg["end"]
        })
        ids.append(f"{audio_id}_seg_{idx}")
        
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

def search_audio_context(query: str, n_results: int = 3):
    """Realiza busca semântica na base de áudios indexados."""
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    formatted_results = []
    if results and "documents" in results and results["documents"]:
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        for doc, meta in zip(docs, metas):
            formatted_results.append({
                "text": doc,
                "start": meta["start"],
                "end": meta["end"],
                "audio_id": meta["audio_id"]
            })
            
    return formatted_results