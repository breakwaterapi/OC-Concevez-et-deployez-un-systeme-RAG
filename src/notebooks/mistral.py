import time

from langchain_core.embeddings import Embeddings
from mistralai import Mistral

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2


class MistralEmbeddings(Embeddings):
    DIMENSION = 1024

    def __init__(self, api_key: str, model: str = "mistral-embed", batch_size: int = 32):
        self.client = Mistral(api_key=api_key)
        self.model = model
        self.batch_size = batch_size

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        valid = [t.strip() for t in texts if t and t.strip()]
        if not valid:
            raise ValueError("No valid texts to embed.")

        all_embeddings: list[list[float]] = []
        for i in range(0, len(valid), self.batch_size):
            batch = valid[i : i + self.batch_size]
            resp = self._call_with_retry(batch)
            if not resp or not resp.data:
                raise RuntimeError("Mistral returned no embedding data.")
            for item in resp.data:
                if item.embedding is None:
                    raise RuntimeError("Mistral returned a null embedding.")
                all_embeddings.append(list(item.embedding))
        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def _call_with_retry(self, batch: list[str]):
        for attempt in range(MAX_RETRIES):
            try:
                return self.client.embeddings.create(model=self.model, inputs=batch)
            except Exception as e:
                if "429" in str(e) and attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2**attempt)
                    time.sleep(delay)
                else:
                    raise
