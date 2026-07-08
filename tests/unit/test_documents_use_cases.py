from unittest.mock import MagicMock

import pytest

from api.common.exceptions import IndexNotReadyError
from api.modules.documents.exceptions import DocumentNotFoundError
from api.modules.documents.use_cases import DocumentsUseCase


@pytest.fixture
def mock_store():
    mock = MagicMock()
    mock.is_ready = True
    mock.list_parent_docs.return_value = [("uid-1", "Texte 1"), ("uid-2", "Texte 2")]
    mock.get_parent_doc.return_value = "Texte 1"
    mock.search_parent_docs.return_value = [("uid-1", "Texte 1")]
    return mock


@pytest.fixture
def use_case(mock_store):
    return DocumentsUseCase(store=mock_store, default_k=5)


def test_list_documents_wraps_tuples_into_parent_documents(use_case):
    docs = use_case.list_documents()

    assert len(docs) == 2
    assert docs[0].uid == "uid-1"
    assert docs[0].text == "Texte 1"
    assert docs[1].uid == "uid-2"


def test_get_document_returns_parent_document(use_case, mock_store):
    doc = use_case.get_document("uid-1")

    assert doc.uid == "uid-1"
    assert doc.text == "Texte 1"
    mock_store.get_parent_doc.assert_called_once_with("uid-1")


def test_get_document_raises_when_not_found(use_case, mock_store):
    mock_store.get_parent_doc.return_value = None

    with pytest.raises(DocumentNotFoundError):
        use_case.get_document("unknown")


def test_retrieve_wraps_tuples_and_uses_default_k(use_case, mock_store):
    docs = use_case.retrieve("concert jazz")

    assert len(docs) == 1
    assert docs[0].uid == "uid-1"
    mock_store.search_parent_docs.assert_called_once_with("concert jazz", k=5)


def test_retrieve_uses_explicit_k(use_case, mock_store):
    use_case.retrieve("concert jazz", k=2)

    mock_store.search_parent_docs.assert_called_once_with("concert jazz", k=2)


def test_retrieve_raises_when_index_not_ready(use_case, mock_store):
    mock_store.is_ready = False

    with pytest.raises(IndexNotReadyError):
        use_case.retrieve("concert jazz")
