from dataclasses import dataclass, field

from loguru import logger
from mistralai.client import Mistral
from mistralai.client.utils import BackoffStrategy, RetryConfig
from tqdm import tqdm

# Native SDK retry: retries on 429/500/502/503/504, honors the Retry-After header when present,
# otherwise a real exponential backoff (2s -> 30s cap) with a 180s total budget per batch.
_RETRY_CONFIG = RetryConfig(
    "backoff",
    BackoffStrategy(
        initial_interval=2000, max_interval=30000, exponent=2, max_elapsed_time=180000
    ),
    retry_connection_errors=False,
)


@dataclass
class MistralEmbedder:
    DIMENSION = 1024

    api_key: str
    model: str = "mistral-embed"
    batch_size: int = 32
    client: Mistral = field(init=False, repr=False)

    def __post_init__(self):
        self.client = Mistral(api_key=self.api_key, retry_config=_RETRY_CONFIG)

    @property
    def dimension(self) -> int:
        return self.DIMENSION

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        valid = [t.strip() for t in texts if t and t.strip()]
        if not valid:
            raise ValueError("No valid texts to embed.")

        all_embeddings: list[list[float]] = []
        batch_starts = range(0, len(valid), self.batch_size)
        for i in tqdm(batch_starts, desc="Embedding chunks", unit="batch"):
            batch = valid[i : i + self.batch_size]
            response = self.client.embeddings.create(model=self.model, inputs=batch)
            if not response or not response.data:
                raise RuntimeError("Mistral returned no embedding data.")

            for item in response.data:
                embedding = item.embedding
                if embedding is None:
                    raise RuntimeError("Mistral returned a null embedding.")
                if len(embedding) != self.DIMENSION:
                    raise ValueError(
                        f"Expected {self.DIMENSION}-dim embedding, got {len(embedding)}"
                    )
                all_embeddings.append(list(embedding))

            logger.debug(f"Embedded batch {i // self.batch_size + 1}, {len(batch)} texts")

        return all_embeddings

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]
