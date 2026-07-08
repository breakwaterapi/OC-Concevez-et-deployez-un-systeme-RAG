"""
End-to-end RAG pipeline test — runs against the real Mistral API and local FAISS index.

Skipped automatically when MISTRAL_API_KEY is not set. Run with:
    uv run pytest tests/integration/ -v -m integration
"""
import os
from pathlib import Path

import pytest

INDEX_PATH = Path(__file__).parent.parent.parent / "models" / "faiss_index"

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def use_case():
    if not os.getenv("MISTRAL_API_KEY"):
        pytest.skip("MISTRAL_API_KEY not set")
    if not INDEX_PATH.exists():
        pytest.skip(f"FAISS index not found at {INDEX_PATH} — run /rebuild first")

    from api.infra.faiss.store import FAISSClient
    from api.infra.mistral.embeddings import MistralEmbedder
    from api.infra.mistral.llm import MistralLLM
    from api.modules.rag.use_cases import AskQuestionUseCase

    api_key = os.environ["MISTRAL_API_KEY"]
    embedder = MistralEmbedder(api_key=api_key, model="mistral-embed")
    faiss_client = FAISSClient(
        embed_texts_fn=embedder.embed_texts,
        embed_query_fn=embedder.embed_query,
    )
    faiss_client.load(str(INDEX_PATH))

    llm = MistralLLM(api_key=api_key, model="mistral-small-latest", temperature=0.0)

    return AskQuestionUseCase(
        vector_store=faiss_client,
        llm=llm,
        retrieval_k=5,
    )


@pytest.mark.parametrize("question", [
    "Quels concerts sont prévus en Île-de-France ?",
    "Y a-t-il des expositions accessibles aux enfants ?",
    "Quels événements ont lieu à Paris ce mois-ci ?",
])
def test_rag_returns_non_empty_answer(use_case, question):
    result = use_case.execute(question)

    assert result.question == question
    assert result.answer, "Answer should not be empty"
    assert len(result.answer) > 10, "Answer should be substantive"


def test_rag_returns_sources_with_uid_and_text(use_case):
    result = use_case.execute("Quels événements ont lieu à Paris ?")

    assert result.sources, "Expected at least one source for a broad query"
    for source in result.sources:
        assert source.uid, "Source uid should not be empty"
        assert source.text, "Source text should not be empty"


def test_rag_empty_question_raises(use_case):
    from api.modules.rag.exceptions import EmptyQuestionError

    with pytest.raises(EmptyQuestionError):
        use_case.execute("")
