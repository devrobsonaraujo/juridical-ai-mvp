from chromadb import PersistentClient
from openai import OpenAI
from app.config import settings

client = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

db_client = PersistentClient(path="./chroma_db")
collection = db_client.get_or_create_collection(name="juridical_audio_index")

def index_transcript_segments(audio_filename: str, segments: list) -> dict:
    """
    Indexa os segmentos da transcrição (com timestamps) no ChromaDB.
    Nome padronizado para atender à chamada do audio_router.
    """
    documents = []
    metadatas = []
    ids = []
    
    for idx, seg in enumerate(segments):
        doc_text = seg.get("text", "")
        if not doc_text.strip():
            continue
            
        documents.append(doc_text)
        metadatas.append({
            "audio_filename": audio_filename,
            "start": float(seg.get("start", 0.0)),
            "end": float(seg.get("end", 0.0))
        })
        ids.append(f"{audio_filename}_seg_{idx}")
        
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

def search_audio_context(query: str, n_results: int = 4, audio_filter: str = None):
    """Realiza busca semântica na base de áudios indexados, com opção de filtro por arquivo."""
    where_clause = {"audio_filename": audio_filter} if audio_filter and audio_filter != "Todos os Áudios" else None
    
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
                "start": meta["start"],
                "end": meta["end"],
                "audio_filename": meta["audio_filename"]
            })
            
    return formatted_results

def query_rag_audio(question: str, k: int = 4, audio_filter: str = None) -> dict:
    """Executa a busca RAG considerando o filtro opcional de áudio."""
    context_segments = search_audio_context(query=question, n_results=k, audio_filter=audio_filter)
    
    context_text = "\n".join([
        f"[{int(s['start']//60):02d}:{int(s['start']%60):02d}] ({s['audio_filename']}): {s['text']}" 
        for s in context_segments
    ])
    
    prompt = f"""
    Com base estritamente nos trechos da audiência judicial abaixo, responda à pergunta formulada indicando os timestamps e o arquivo de origem.
    
    Trechos das Audiências:
    {context_text}
    
    Pergunta: {question}
    """
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    answer = response.choices[0].message.content
    
    return {
        "answer": answer,
        "sources": context_segments
    }

def query_rag_audio(question: str, k: int = 4, audio_filter: str = None) -> dict:
    """
    Executa a busca RAG considerando o filtro opcional de áudio.
    """
    context_segments = search_audio_context(query=question, n_results=k, audio_filter=audio_filter)
    
    context_text = "\n".join([
        f"[{int(s['start']//60):02d}:{int(s['start']%60):02d}] ({s['audio_filename']}): {s['text']}" 
        for s in context_segments
    ])
    
    prompt = f"""
    Com base estritamente nos trechos da audiência judicial abaixo, responda à pergunta formulada indicando os timestamps e o arquivo de origem.
    
    Trechos das Audiências:
    {context_text}
    
    Pergunta: {question}
    """
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",  # Modelo verificado diretamente no seu painel da Groq
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    answer = response.choices[0].message.content
    
    return {
        "answer": answer,
        "sources": context_segments
    }