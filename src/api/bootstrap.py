from api.common.config import get_settings
from api.infra.faiss.store import FAISSClient
from api.infra.mistral.embeddings import MistralEmbedder
from api.modules.health.adapters import MistralModelChecker
from api.modules.health.use_cases import HealthUseCases

_faiss_client: FAISSClient | None = None
_health_use_cases: HealthUseCases | None = None


def bootstrap() -> None:
    global _faiss_client, _health_use_cases
    s = get_settings()

    embedder = MistralEmbedder(api_key=s.mistral_api_key, model=s.mistral_embed_model)
    faiss_client = FAISSClient(
        embed_texts_fn=embedder.embed_texts,
        embed_query_fn=embedder.embed_query,
    )
    try:
        faiss_client.load(str(s.faiss_index_path))
    except FileNotFoundError:
        pass
    _faiss_client = faiss_client

    _health_use_cases = HealthUseCases(
        store_checker=faiss_client,
        model_checker=MistralModelChecker(api_key=s.mistral_api_key),
    )


def get_faiss_client() -> FAISSClient:
    if _faiss_client is None:
        raise RuntimeError("FAISSClient is not initialized. Call bootstrap() first.")
    return _faiss_client


def get_health_use_cases() -> HealthUseCases:
    if _health_use_cases is None:
        raise RuntimeError("HealthUseCases is not initialized. Call bootstrap() first.")
    return _health_use_cases
