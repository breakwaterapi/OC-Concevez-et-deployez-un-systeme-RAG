from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api.bootstrap import get_data_use_cases
from api.common.security import get_settings
from api.main import app


@pytest.fixture
def auth_client(monkeypatch, mock_data_use_cases):
    """A client that exercises the real verify_rebuild_api_key dependency (not overridden)."""
    settings = get_settings()
    monkeypatch.setattr(settings, "rebuild_api_key", "test-secret")

    monkeypatch.setattr("api.main.bootstrap", lambda: None)
    monkeypatch.setattr("api.main.get_faiss_client", lambda: MagicMock(is_ready=False))
    app.dependency_overrides[get_data_use_cases] = lambda: mock_data_use_cases

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_rebuild_without_api_key_is_rejected(auth_client):
    response = auth_client.post("/rebuild")

    assert response.status_code == 401


def test_rebuild_with_wrong_api_key_is_rejected(auth_client):
    response = auth_client.post("/rebuild", headers={"X-API-Key": "wrong"})

    assert response.status_code == 401


def test_rebuild_with_correct_api_key_succeeds(auth_client):
    response = auth_client.post("/rebuild", headers={"X-API-Key": "test-secret"})

    assert response.status_code == 200
