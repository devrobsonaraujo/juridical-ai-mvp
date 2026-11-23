
import math
from functools import lru_cache

from app.config import settings
from app.services.embedding_provider import EmbeddingProvider


class EmbeddingService:
    """
    Serviço local de embeddings multilíngues E5.

    - Carregamento sob demanda.
    - Reutilização do modelo em memória.
    - Processamento em lotes.
    - Normalização dos embeddings.
    - Validação de dimensão e valores numéricos.

    Prefixos E5:
    - passage: documentos
    - query: perguntas
    """

    def __init__(
        self,
        model_name: str | None = None,
        batch_size: int | None = None,
    ):
        self.model_name = (
            model_name or settings.EMBEDDING_MODEL
        )

        self.batch_size = (
            batch_size
            if batch_size is not None
            else settings.EMBEDDING_BATCH_SIZE
        )

        if not isinstance(self.batch_size, int):
            raise ValueError(
                "O tamanho do lote deve ser um inteiro."
            )

        if self.batch_size < 1:
            raise ValueError(
                "O tamanho do lote deve ser positivo."
            )

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_model(model_name: str):
        """
        Importa e carrega o modelo apenas na
        primeira utilização.

        O cache evita recarregar os pesos em
        consultas subsequentes.
        """
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(model_name)

    @staticmethod
    def _validate_texts(texts: list[str]) -> None:
        if not isinstance(texts, list):
            raise ValueError(
                "Os textos devem ser fornecidos em uma lista."
            )

        if any(
            not isinstance(text, str) or not text.strip()
            for text in texts
        ):
            raise ValueError(
                "Os textos devem ser strings não vazias."
            )

    @staticmethod
    def _validate_vectors(
        vectors: list[list[float]],
        expected_count: int,
    ) -> list[list[float]]:
        if len(vectors) != expected_count:
            raise ValueError(
                "Quantidade inesperada de embeddings."
            )

        validated = []

        for vector in vectors:
            if len(vector) != settings.EMBEDDING_DIMENSIONS:
                raise ValueError(
                    "Dimensão inesperada do embedding. "
                    f"Esperado: {settings.EMBEDDING_DIMENSIONS}; "
                    f"recebido: {len(vector)}."
                )

            numeric_vector = []

            for value in vector:
                number = float(value)

                if not math.isfinite(number):
                    raise ValueError(
                        "O embedding contém valores inválidos."
                    )

                numeric_vector.append(number)

            validated.append(numeric_vector)

        return validated

    def _encode(
        self,
        texts: list[str],
        prefix: str,
    ) -> list[list[float]]:
        self._validate_texts(texts)

        if not texts:
            return []

        model = self._load_model(self.model_name)
        results = []

        for start in range(0, len(texts), self.batch_size):
            batch = texts[start:start + self.batch_size]

            prepared = [
                f"{prefix}: {text.strip()}"
                for text in batch
            ]

            vectors = model.encode(
                prepared,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            validated = self._validate_vectors(
                vectors.tolist(),
                expected_count=len(batch),
            )

            results.extend(validated)

        return results

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return self._encode(texts, "passage")

    def embed_query(
        self,
        question: str,
    ) -> list[float]:
        vectors = self._encode(
            [question],
            "query",
        )

        return vectors[0]


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingProvider:
    """
    Factory central de embeddings.

    O provedor local permanece como padrão.
    Outros provedores poderão ser adicionados
    posteriormente sem alterar os consumidores.
    """
    provider = settings.EMBEDDING_PROVIDER.strip().lower()

    if provider == "local":
        return EmbeddingService()

    raise ValueError(
        f"Provedor de embeddings não suportado: {provider}"
    )
