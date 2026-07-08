from unittest.mock import MagicMock

import pytest

from api.common.exceptions import IndexNotReadyError
from api.modules.rag.entities import RAGResponse
from api.modules.rag.exceptions import EmptyQuestionError
from api.modules.rag.use_cases import AskQuestionUseCase


@pytest.fixture
def mock_vector_store():
    mock = MagicMock()
    mock.is_ready = True
    mock.search_parent_docs.return_value = [("ev1", "Texte événement")]
    return mock


@pytest.fixture
def mock_llm():
    mock = MagicMock()
    mock.invoke.return_value = "Voici une réponse test."
    return mock


@pytest.fixture
def use_case(mock_vector_store, mock_llm):
    return AskQuestionUseCase(vector_store=mock_vector_store, llm=mock_llm, retrieval_k=3)


def test_execute_returns_rag_response(use_case, mock_vector_store, mock_llm):
    result = use_case.execute("Quels sont les concerts ce week-end ?")

    assert isinstance(result, RAGResponse)
    assert result.question == "Quels sont les concerts ce week-end ?"
    assert result.answer == "Voici une réponse test."
    assert len(result.sources) == 1
    assert result.sources[0].uid == "ev1"
    assert result.sources[0].text == "Texte événement"
    mock_vector_store.search_parent_docs.assert_called_once_with(
        "Quels sont les concerts ce week-end ?", k=3
    )
    mock_llm.invoke.assert_called_once()


def test_execute_llm_called_with_strings(use_case, mock_llm):
    use_case.execute("Quels concerts ce week-end ?")

    args = mock_llm.invoke.call_args
    assert isinstance(args[0][0], str), "system_prompt should be a string"
    assert isinstance(args[0][1], str), "user_message should be a string"


def test_execute_no_documents_returns_fallback(use_case, mock_vector_store):
    mock_vector_store.search_parent_docs.return_value = []

    result = use_case.execute("Question sans résultats")

    assert "aucun événement" in result.answer.lower()
    assert result.sources == []
    mock_llm = use_case.llm
    mock_llm.invoke.assert_not_called()


def test_execute_empty_question_raises(use_case):
    with pytest.raises(EmptyQuestionError):
        use_case.execute("")


def test_execute_whitespace_question_raises(use_case):
    with pytest.raises(EmptyQuestionError):
        use_case.execute("   ")


def test_execute_raises_when_index_not_ready(use_case, mock_vector_store):
    mock_vector_store.is_ready = False

    with pytest.raises(IndexNotReadyError):
        use_case.execute("Quels concerts ce week-end ?")
