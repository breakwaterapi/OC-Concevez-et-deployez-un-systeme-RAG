"""Reduced RAGAS evaluation, meant to run in CI as a coarse non-regression check.

First step is building the Faiss index in memory from a fixed, versioned dataset
(tests/fixtures/documents.json — a copy of the 200-event test corpus' parent documents as plain
JSON, no binary index committed to the repo; this 200-event set is itself already a reduced
dataset — production can go up to OPENAGENDA_MAX_RECORDS=1000). Then runs 4 questions
(data/evaluation/test_questions_ci.json, one of them about an event absent from the corpus) to
keep the number of Mistral chat/judge calls low — the free tier has a strict requests-per-second
limit and GitHub Actions has a limited run time (the one-off embedding pass to build the index is
the same cost as any `/rebuild` call).

Skipped automatically when MISTRAL_API_KEY is not set. Run manually with:
    uv run pytest tests/eval/ -v -m ragas_ci
"""

import json
import os
from pathlib import Path

import pytest

# ragas 0.4.x still supports these imports/wrappers but warns about the future
# ragas.metrics.collections / llm_factory API — silenced here to keep CI output readable, same
# trade-off as notebooks 06/07 (see their config cells for the same note). Not a real migration:
# the new API drops the batch evaluate(dataset=..., metrics=[...]) harness this file relies on in
# favor of per-sample scoring, and its embedding_factory has no documented Mistral provider.
#
# Plain warnings.filterwarnings() at import time does NOT work here: pytest's warnings plugin
# wraps each test in its own catch_warnings()/simplefilter context and resets filters before the
# test (and its fixtures) run, wiping anything registered at collection time. pytest.mark
# .filterwarnings is applied by that same plugin, so it survives. The `module` field is also
# unreliable: these libraries warn with a stacklevel pointing at the caller, so the reported
# module is this test file, not ragas/langchain — matching on the message is what actually works.
# One broad substring match (like notebooks 06/07's message=r".*ragas.*") rather than one entry
# per exact deprecation string: every ragas/Langchain-wrapper deprecation message here references
# a ragas.* module or docs.ragas.io, so this survives ragas rewording its messages instead of
# silently stopping mid-suppression the day the exact text changes.
pytestmark = [
    pytest.mark.ragas_ci,
    pytest.mark.filterwarnings(r"ignore:.*ragas.*:DeprecationWarning"),
]

DOCUMENTS_PATH = Path(__file__).parent.parent / "fixtures" / "documents.json"
CI_QUESTIONS_PATH = (
    Path(__file__).parent.parent.parent / "data" / "evaluation" / "test_questions_ci.json"
)

# Coarse thresholds: this is a smoke check, not a quality gate — it should only fail loudly on
# an actual regression (e.g. broken prompt, broken retrieval), not on minor score fluctuations.
MIN_FAITHFULNESS = 0.5
MIN_ANSWER_RELEVANCY = 0.5


@pytest.fixture(scope="module")
def faiss_client():
    """Build the Faiss index once, in memory, from the committed dataset (no disk persistence,
    no binary files — this is the "faire l'indexation faiss une fois" step)."""
    if not os.getenv("MISTRAL_API_KEY"):
        pytest.skip("MISTRAL_API_KEY not set")

    from api.infra.faiss.store import FAISSClient
    from api.infra.mistral.embeddings import MistralEmbedder
    from api.infra.preprocessing.chunker import TextChunker

    api_key = os.environ["MISTRAL_API_KEY"]
    documents: dict[str, str] = json.loads(DOCUMENTS_PATH.read_text(encoding="utf-8"))

    chunker = TextChunker()
    texts: list[str] = []
    metadatas: list[dict[str, str]] = []
    for uid, text in documents.items():
        for i, fragment in enumerate(chunker.split_text(text)):
            texts.append(fragment)
            metadatas.append({"uid": uid, "chunk_id": str(i)})

    embedder = MistralEmbedder(api_key=api_key, model="mistral-embed")
    embeddings = embedder.embed_texts(texts)

    client = FAISSClient(embed_texts_fn=embedder.embed_texts, embed_query_fn=embedder.embed_query)
    client.build(texts, embeddings, metadatas, documents)
    return client


@pytest.fixture(scope="module")
def rag_use_case(faiss_client):
    from api.infra.mistral.llm import MistralLLM
    from api.modules.rag.use_cases import AskQuestionUseCase

    api_key = os.environ["MISTRAL_API_KEY"]
    llm = MistralLLM(api_key=api_key, model="mistral-small-latest", temperature=0.0)

    return AskQuestionUseCase(
        vector_store=faiss_client,
        llm=llm,
        retrieval_k=5,
    )


@pytest.fixture(scope="module")
def scores_df(rag_use_case):
    from typing import cast

    from langchain_core.rate_limiters import InMemoryRateLimiter
    from langchain_mistralai import ChatMistralAI
    from ragas import RunConfig, evaluate
    from ragas.dataset_schema import EvaluationDataset, EvaluationResult
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        AnswerRelevancy,
        ContextEntityRecall,
        ContextPrecision,
        ContextRecall,
        Faithfulness,
    )

    from notebooks.mistral import MistralEmbeddings

    api_key = os.environ["MISTRAL_API_KEY"]
    questions = json.loads(CI_QUESTIONS_PATH.read_text(encoding="utf-8"))

    results = []
    for item in questions:
        response = rag_use_case.execute(item["question"])
        results.append(
            {
                "user_input": item["question"],
                "retrieved_contexts": [s.text for s in response.sources],
                "response": response.answer,
                "reference": item["reference"],
            }
        )

    rate_limiter = InMemoryRateLimiter(
        requests_per_second=0.3, check_every_n_seconds=1, max_bucket_size=1
    )
    judge_llm = ChatMistralAI(
        model="mistral-medium-latest",  # pyright: ignore[reportCallIssue]
        mistral_api_key=api_key,  # pyright: ignore[reportCallIssue]
        temperature=0.0,
        rate_limiter=rate_limiter,
    )
    judge_embeddings = MistralEmbeddings(api_key=api_key, model="mistral-embed")

    evaluator_llm = LangchainLLMWrapper(judge_llm)
    evaluator_embeddings = LangchainEmbeddingsWrapper(judge_embeddings)

    # evaluate() returns EvaluationResult | Executor depending on return_executor, which we never
    # pass (defaults to False) — always an EvaluationResult here, but ragas has no overload keyed
    # on that literal default, so the type checker can't narrow it on its own.
    eval_result = cast(
        EvaluationResult,
        evaluate(
            dataset=EvaluationDataset.from_list(results),
            metrics=[
                Faithfulness(llm=evaluator_llm),
                AnswerRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings, strictness=1),
                ContextRecall(llm=evaluator_llm),
                ContextPrecision(llm=evaluator_llm),
                ContextEntityRecall(llm=evaluator_llm),
            ],
            llm=evaluator_llm,
            embeddings=evaluator_embeddings,
            run_config=RunConfig(timeout=300, max_workers=1, max_wait=60, max_retries=2),
        ),
    )
    return eval_result.to_pandas()


def test_ragas_ci_faithfulness_above_threshold(scores_df):
    mean_faithfulness = scores_df["faithfulness"].mean()

    assert mean_faithfulness >= MIN_FAITHFULNESS, (
        f"Mean faithfulness {mean_faithfulness:.2f} below smoke threshold {MIN_FAITHFULNESS} — "
        "possible regression in prompt/retrieval."
    )


def test_ragas_ci_answer_relevancy_above_threshold(scores_df):
    mean_relevancy = scores_df["answer_relevancy"].mean()

    assert mean_relevancy >= MIN_ANSWER_RELEVANCY, (
        f"Mean answer_relevancy {mean_relevancy:.2f} below smoke threshold "
        f"{MIN_ANSWER_RELEVANCY} — possible regression in prompt/generation."
    )
