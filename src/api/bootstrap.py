from api.common.config import get_settings
from api.infra.faiss.store import FAISSClient
from api.infra.mistral.embeddings import MistralEmbedder
from api.modules.health.adapters import MistralModelChecker
from api.modules.health.use_cases import HealthUseCases
from api.modules.metadata.use_cases import MetadataUseCases

_faiss_client: FAISSClient | None = None
_health_use_cases: HealthUseCases | None = None
_metadata_use_cases: MetadataUseCases | None = None


def bootstrap() -> None:
    global _faiss_client, _health_use_cases, _metadata_use_cases
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

    _metadata_use_cases = MetadataUseCases(
        index_info=faiss_client,
        region=s.openagenda_region,
        date_from=s.date_from,
        date_to=s.date_to,
        embed_model=s.mistral_embed_model,
        chat_model=s.mistral_chat_model,
    )


def get_faiss_client() -> FAISSClient:
    if _faiss_client is None:
        raise RuntimeError("FAISSClient is not initialized. Call bootstrap() first.")
    return _faiss_client


def get_health_use_cases() -> HealthUseCases:
    if _health_use_cases is None:
        raise RuntimeError("HealthUseCases is not initialized. Call bootstrap() first.")
    return _health_use_cases


def get_metadata_use_cases() -> MetadataUseCases:
    if _metadata_use_cases is None:
        raise RuntimeError("MetadataUseCases is not initialized. Call bootstrap() first.")
    return _metadata_use_cases
