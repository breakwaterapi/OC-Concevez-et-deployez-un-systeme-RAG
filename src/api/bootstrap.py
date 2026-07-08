from api.common.config import get_settings
from api.infra.faiss.store import FAISSClient
from api.infra.mistral.embeddings import MistralEmbedder
from api.infra.mistral.llm import MistralLLM
from api.infra.openagenda.client import OpenAgendaClient
from api.infra.preprocessing.chunker import TextChunker
from api.infra.preprocessing.cleaner import DoclingCleaner
from api.modules.data.adapters import FAISSIndexBuilderAdapter, LangChainChunkerAdapter
from api.modules.data.use_cases import BuildIndexUseCase, DataUseCases, PrepareDataUseCase
from api.modules.documents.use_cases import DocumentsUseCase
from api.modules.health.adapters import MistralModelChecker
from api.modules.health.use_cases import HealthUseCases
from api.modules.metadata.use_cases import MetadataUseCases
from api.modules.rag.use_cases import AskQuestionUseCase

_faiss_client: FAISSClient | None = None
_rag_use_case: AskQuestionUseCase | None = None
_documents_use_case: DocumentsUseCase | None = None
_health_use_cases: HealthUseCases | None = None
_data_use_cases: DataUseCases | None = None
_metadata_use_cases: MetadataUseCases | None = None


def bootstrap() -> None:
    global _faiss_client, _rag_use_case, _documents_use_case
    global _health_use_cases, _data_use_cases, _metadata_use_cases
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

    llm = MistralLLM(
        api_key=s.mistral_api_key,
        model=s.mistral_chat_model,
        temperature=s.mistral_temperature,
    )

    _rag_use_case = AskQuestionUseCase(
        vector_store=faiss_client,
        llm=llm,
        retrieval_k=s.retrieval_k,
    )

    _documents_use_case = DocumentsUseCase(
        store=faiss_client,
        default_k=s.retrieval_k,
    )

    _health_use_cases = HealthUseCases(
        store_checker=faiss_client,
        model_checker=MistralModelChecker(api_key=s.mistral_api_key),
    )

    where_clause = OpenAgendaClient.build_where_clause(
        region=s.openagenda_region,
        date_from=s.date_from,
        date_to=s.date_to,
    )
    _data_use_cases = DataUseCases(
        prepare=PrepareDataUseCase(
            fetcher=OpenAgendaClient(base_url=s.openagenda_base_url),
            cleaner=DoclingCleaner(),
            where_clause=where_clause,
            max_records=s.openagenda_max_records,
        ),
        build_index=BuildIndexUseCase(
            chunker=LangChainChunkerAdapter(
                text_chunker=TextChunker(
                    chunk_max_tokens=s.chunk_max_tokens,
                    chunk_overlap_tokens=s.chunk_overlap_tokens,
                ),
            ),
            embedder=embedder,
            index_builder=FAISSIndexBuilderAdapter(faiss_client=faiss_client),
            index_path=str(s.faiss_index_path),
        ),
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


def get_rag_use_case() -> AskQuestionUseCase:
    if _rag_use_case is None:
        raise RuntimeError("AskQuestionUseCase is not initialized. Call bootstrap() first.")
    return _rag_use_case


def get_documents_use_case() -> DocumentsUseCase:
    if _documents_use_case is None:
        raise RuntimeError("DocumentsUseCase is not initialized. Call bootstrap() first.")
    return _documents_use_case


def get_health_use_cases() -> HealthUseCases:
    if _health_use_cases is None:
        raise RuntimeError("HealthUseCases is not initialized. Call bootstrap() first.")
    return _health_use_cases


def get_metadata_use_cases() -> MetadataUseCases:
    if _metadata_use_cases is None:
        raise RuntimeError("MetadataUseCases is not initialized. Call bootstrap() first.")
    return _metadata_use_cases


def get_data_use_cases() -> DataUseCases:
    if _data_use_cases is None:
        raise RuntimeError("DataUseCases is not initialized. Call bootstrap() first.")
    return _data_use_cases
