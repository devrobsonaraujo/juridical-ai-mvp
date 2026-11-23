
from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """
    Contrato dos provedores de embeddings.

    Qualquer implementação deve retornar vetores
    compatíveis com a dimensão configurada no banco.
    """

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        ...

    def embed_query(
        self,
        question: str,
    ) -> list[float]:
        ...
