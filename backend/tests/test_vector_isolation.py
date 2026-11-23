
import uuid

import pytest

from app.services import vector_service


ADVOGADO_A = "11111111-1111-4111-8111-111111111111"
ADVOGADO_B = "22222222-2222-4222-8222-222222222222"


class FakeCollection:
    """
    Simula a coleção ChromaDB em memória.

    Nenhum dado real é gravado ou consultado.
    """

    def __init__(self):
        self.records = {}

    def add(self, documents, metadatas, ids):
        for document, metadata, record_id in zip(
            documents, metadatas, ids
        ):
            self.records[record_id] = {
                "document": document,
                "metadata": metadata,
            }

    def _matches(self, metadata, where):
        if not where:
            return True

        if "$and" in where:
            return all(
                self._matches(metadata, condition)
                for condition in where["$and"]
            )

        return all(
            metadata.get(key) == value
            for key, value in where.items()
        )

    def get(self, where=None, include=None):
        matches = [
            (record_id, record)
            for record_id, record in self.records.items()
            if self._matches(record["metadata"], where)
        ]

        return {
            "ids": [
                record_id for record_id, _ in matches
            ],
            "metadatas": [
                record["metadata"] for _, record in matches
            ],
            "documents": [
                record["document"] for _, record in matches
            ],
        }

    def query(
        self,
        query_texts,
        n_results,
        where=None,
    ):
        matches = self.get(where=where)

        return {
            "documents": [
                matches["documents"][:n_results]
            ],
            "metadatas": [
                matches["metadatas"][:n_results]
            ],
        }


@pytest.fixture
def fake_collection(monkeypatch):
    fake = FakeCollection()

    monkeypatch.setattr(
        vector_service,
        "collection",
        fake,
    )

    return fake


def make_segments(text):
    return [
        {
            "text": text,
            "start": 10.0,
            "end": 25.0,
        }
    ]


def test_indexacao_registra_proprietario(
    fake_collection,
):
    result = vector_service.index_transcript_segments(
        audio_filename="audiencia.mp3",
        segments=make_segments(
            "Depoimento fictício do advogado A."
        ),
        owner_user_id=ADVOGADO_A,
    )

    assert result["status"] == "indexado"
    assert result["chunks_count"] == 1

    records = list(fake_collection.records.values())

    assert len(records) == 1

    assert (
        records[0]["metadata"]["owner_user_id"]
        == ADVOGADO_A
    )


def test_historico_nao_exibe_arquivos_de_outro_advogado(
    fake_collection,
):
    vector_service.index_transcript_segments(
        "arquivo_a.mp3",
        make_segments("Conteúdo exclusivo do A."),
        ADVOGADO_A,
    )

    vector_service.index_transcript_segments(
        "arquivo_b.mp3",
        make_segments("Conteúdo exclusivo do B."),
        ADVOGADO_B,
    )

    historico_a = (
        vector_service.get_indexed_audio_history(
            ADVOGADO_A
        )
    )

    historico_b = (
        vector_service.get_indexed_audio_history(
            ADVOGADO_B
        )
    )

    assert len(historico_a) == 1
    assert len(historico_b) == 1

    assert historico_a[0]["filename"] == "arquivo_a.mp3"
    assert historico_b[0]["filename"] == "arquivo_b.mp3"


def test_busca_rag_nao_recupera_documentos_de_outro_advogado(
    fake_collection,
):
    vector_service.index_transcript_segments(
        "audiencia_a.mp3",
        make_segments("Informação reservada do A."),
        ADVOGADO_A,
    )

    vector_service.index_transcript_segments(
        "audiencia_b.mp3",
        make_segments("Informação reservada do B."),
        ADVOGADO_B,
    )

    resultados_a = vector_service.search_audio_context(
        query="Qual é a informação?",
        owner_user_id=ADVOGADO_A,
    )

    resultados_b = vector_service.search_audio_context(
        query="Qual é a informação?",
        owner_user_id=ADVOGADO_B,
    )

    assert len(resultados_a) == 1
    assert len(resultados_b) == 1

    assert (
        resultados_a[0]["audio_filename"]
        == "audiencia_a.mp3"
    )

    assert (
        resultados_b[0]["audio_filename"]
        == "audiencia_b.mp3"
    )

    assert "reservada do B" not in resultados_a[0]["text"]
    assert "reservada do A" not in resultados_b[0]["text"]


def test_busca_com_filtro_de_arquivo_mantem_isolamento(
    fake_collection,
):
    # Mesmo nome de arquivo em duas contas diferentes.
    vector_service.index_transcript_segments(
        "mesmo_nome.mp3",
        make_segments("Conteúdo pertencente ao A."),
        ADVOGADO_A,
    )

    vector_service.index_transcript_segments(
        "mesmo_nome.mp3",
        make_segments("Conteúdo pertencente ao B."),
        ADVOGADO_B,
    )

    resultados = vector_service.search_audio_context(
        query="Conteúdo",
        audio_filter="mesmo_nome.mp3",
        owner_user_id=ADVOGADO_B,
    )

    assert len(resultados) == 1
    assert "pertencente ao B" in resultados[0]["text"]
    assert "pertencente ao A" not in resultados[0]["text"]


def test_ids_nao_colidem_quando_arquivos_tem_mesmo_nome(
    fake_collection,
):
    primeiro = vector_service.index_transcript_segments(
        "audiencia.mp3",
        make_segments("Primeira gravação."),
        ADVOGADO_A,
    )

    segundo = vector_service.index_transcript_segments(
        "audiencia.mp3",
        make_segments("Segunda gravação."),
        ADVOGADO_A,
    )

    assert primeiro["media_id"] != segundo["media_id"]
    assert len(fake_collection.records) == 2


@pytest.mark.parametrize(
    "owner_user_id",
    [
        None,
        "",
        "advogado",
        "123",
    ],
)
def test_rejeita_proprietario_invalido(
    fake_collection,
    owner_user_id,
):
    with pytest.raises(ValueError):
        vector_service.search_audio_context(
            query="Teste",
            owner_user_id=owner_user_id,
        )


def test_registros_antigos_sem_proprietario_ficam_isolados(
    fake_collection,
):
    # Simula um registro legado na coleção de teste.
    fake_collection.add(
        documents=["Conteúdo antigo sem proprietário."],
        metadatas=[{
            "audio_filename": "antigo.mp3",
            "start": 0.0,
            "end": 10.0,
        }],
        ids=[str(uuid.uuid4())],
    )

    historico = vector_service.get_indexed_audio_history(
        ADVOGADO_A
    )

    resultados = vector_service.search_audio_context(
        query="Conteúdo antigo",
        owner_user_id=ADVOGADO_A,
    )

    assert historico == []
    assert resultados == []
