from unittest.mock import MagicMock

from fastapi.testclient import TestClient
import pytest

from api.bootstrap import (
    get_data_use_cases,
    get_documents_use_case,
    get_health_use_cases,
    get_metadata_use_cases,
    get_rag_use_case,
)
from api.common.domain.entities import ParentDocument
from api.common.security import verify_rebuild_api_key
from api.main import app
from api.modules.documents.exceptions import DocumentNotFoundError
from api.modules.health.use_cases import HealthStatus
from api.modules.metadata.use_cases import IndexMetadata
from api.modules.rag.entities import RAGResponse


def _raise_not_found(uid: str) -> ParentDocument:
    raise DocumentNotFoundError(uid)


@pytest.fixture
def mock_health_use_cases():
    mock = MagicMock()
    mock.check.return_value = HealthStatus(
        status="ok", store_ready=True, model_ready=True, index_size=42
    )
    return mock


@pytest.fixture
def mock_metadata_use_cases():
    mock = MagicMock()
    mock.get.return_value = IndexMetadata(
        region="Île-de-France",
        date_from="2025-06-01T00:00:00Z",
        date_to="2027-06-01T00:00:00Z",
        n_events=200,
        n_chunks=350,
        embed_model="mistral-embed",
        chat_model="mistral-small-latest",
    )
    return mock


@pytest.fixture
def mock_data_use_cases():
    mock = MagicMock()
    mock.prepare.execute.return_value = []
    mock.build_index.execute.return_value = (10, 3)
    return mock


@pytest.fixture
def mock_rag_use_case():
    mock = MagicMock()
    mock.execute.return_value = RAGResponse(
        question="Test ?",
        answer="Réponse test.",
        sources=[ParentDocument(uid="uid-1", text="Texte source.")],
    )
    return mock


@pytest.fixture
def mock_documents_use_case():
    mock = MagicMock()
    mock.list_documents.return_value = [
        ParentDocument(uid="uid-1", text="Texte source."),
        ParentDocument(uid="uid-2", text="Autre source."),
    ]
    mock.get_document.side_effect = lambda uid: (
        ParentDocument(uid="uid-1", text="Texte source.")
        if uid == "uid-1"
        else _raise_not_found(uid)
    )
    mock.retrieve.return_value = [ParentDocument(uid="uid-1", text="Texte source.")]
    return mock


@pytest.fixture
def client(
    monkeypatch,
    mock_rag_use_case,
    mock_documents_use_case,
    mock_health_use_cases,
    mock_data_use_cases,
    mock_metadata_use_cases,
):
    monkeypatch.setattr("api.main.bootstrap", lambda: None)
    monkeypatch.setattr("api.main.get_faiss_client", lambda: MagicMock(is_ready=False))

    app.dependency_overrides[get_rag_use_case] = lambda: mock_rag_use_case
    app.dependency_overrides[get_documents_use_case] = lambda: mock_documents_use_case
    app.dependency_overrides[get_health_use_cases] = lambda: mock_health_use_cases
    app.dependency_overrides[get_data_use_cases] = lambda: mock_data_use_cases
    app.dependency_overrides[get_metadata_use_cases] = lambda: mock_metadata_use_cases
    app.dependency_overrides[verify_rebuild_api_key] = lambda: None

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
