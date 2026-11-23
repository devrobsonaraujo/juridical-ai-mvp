
import uuid
from collections import defaultdict

from chromadb import PersistentClient

from app.services.chunking_service import chunk_segments


# Coleção antiga:
# juridical_audio_index
#
# Ela será preservada, mas não utilizada pela aplicação.
#
# A coleção v2 recebe somente documentos que possuem
# um proprietário autenticado.

db_client = PersistentClient(path="./chroma_db")

collection = db_client.get_or_create_collection(
    name="juridical_audio_index_v2"
)


def _validate_owner(owner_user_id: str) -> str:
    """
    Impede consultas ou gravações sem proprietário.

    O identificador deve ser fornecido pelo backend
    após validação da sessão, nunca pelo navegador.
    """
    if not isinstance(owner_user_id, str):
        raise ValueError(
            "O identificador do advogado é obrigatório."
        )

    try:
        return str(uuid.UUID(owner_user_id))
    except (ValueError, AttributeError) as exc:
        raise ValueError(
            "Identificador do advogado inválido."
        ) from exc


def index_transcript_segments(
    audio_filename: str,
    segments: list,
    owner_user_id: str,
) -> dict:
    """
    Indexa uma transcrição com proprietário obrigatório.

    Cada upload recebe um media_id exclusivo, evitando
    colisões quando arquivos possuem o mesmo nome.
    """
    owner_id = _validate_owner(owner_user_id)

    contextual_chunks = chunk_segments(
        segments,
        max_words=120,
        overlap_words=25,
    )

    media_id = str(uuid.uuid4())

    documents = []
    metadatas = []
    ids = []

    for idx, chunk in enumerate(contextual_chunks):
        documents.append(chunk["text"])

        metadatas.append({
            "owner_user_id": owner_id,
            "media_id": media_id,
            "audio_filename": audio_filename,
            "start": float(chunk["start"]),
            "end": float(chunk["end"]),
        })

        ids.append(
            f"{media_id}_chunk_{idx}"
        )

    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    return {
        "status": "indexado",
        "chunks_count": len(documents),
        "media_id": media_id,
    }


def search_audio_context(
    query: str,
    n_results: int = 6,
    audio_filter: str | None = None,
    owner_user_id: str | None = None,
) -> list:
    """
    Busca semântica restrita ao advogado autenticado.

    O filtro de proprietário é sempre obrigatório.
    O filtro de arquivo é apenas complementar.
    """
    owner_id = _validate_owner(owner_user_id)

    if not isinstance(query, str) or not query.strip():
        raise ValueError(
            "A pergunta não pode estar vazia."
        )

    if not 1 <= n_results <= 20:
        raise ValueError(
            "n_results deve estar entre 1 e 20."
        )

    owner_filter = {
        "owner_user_id": owner_id
    }

    if (
        audio_filter
        and audio_filter not in (
            "Todos os Áudios",
            "Todas as Mídias",
        )
    ):
        where_clause = {
            "$and": [
                owner_filter,
                {
                    "audio_filename": audio_filter
                },
            ]
        }
    else:
        where_clause = owner_filter

    # Consulta apenas registros pertencentes ao usuário.
    # Caso não existam, evita uma busca desnecessária.
    matching = collection.get(
        where=where_clause,
        include=["metadatas"],
    )

    matching_ids = matching.get("ids") or []

    if not matching_ids:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(
            n_results,
            len(matching_ids),
        ),
        where=where_clause,
    )

    formatted_results = []

    documents = results.get("documents") or []
    metadatas = results.get("metadatas") or []

    if not documents or not metadatas:
        return []

    for doc, meta in zip(
        documents[0],
        metadatas[0],
    ):
        if not meta:
            continue

        # Verificação adicional de defesa.
        if meta.get("owner_user_id") != owner_id:
            continue

        formatted_results.append({
            "text": doc,
            "start": meta.get("start", 0.0),
            "end": meta.get("end", 0.0),
            "audio_filename": meta.get(
                "audio_filename",
                "Mídia",
            ),
            "media_id": meta.get("media_id", ""),
        })

    return formatted_results


def get_indexed_audio_history(
    owner_user_id: str,
) -> list:
    """
    Retorna exclusivamente as mídias do advogado.

    Agrupa por media_id, permitindo que dois uploads
    tenham o mesmo nome sem serem confundidos.
    """
    owner_id = _validate_owner(owner_user_id)

    data = collection.get(
        where={
            "owner_user_id": owner_id
        },
        include=[
            "metadatas",
            "documents",
        ],
    )

    metadatas = data.get("metadatas") or []
    documents = data.get("documents") or []

    media_map = defaultdict(
        lambda: {
            "filename": "",
            "chunks_count": 0,
            "preview": "",
            "media_id": "",
        }
    )

    for meta, document in zip(
        metadatas,
        documents,
    ):
        if not meta:
            continue

        if meta.get("owner_user_id") != owner_id:
            continue

        media_id = meta.get("media_id")

        if not media_id:
            continue

        item = media_map[media_id]

        item["media_id"] = media_id
        item["filename"] = meta.get(
            "audio_filename",
            "Mídia",
        )

        item["chunks_count"] += 1

        if not item["preview"]:
            item["preview"] = (
                document or ""
            )[:100]

    return list(media_map.values())
