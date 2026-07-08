from unittest.mock import MagicMock

from fastapi.testclient import TestClient
import pytest

from api.bootstrap import get_health_use_cases
from api.main import app
from api.modules.health.use_cases import HealthStatus


@pytest.fixture
def mock_health_use_cases():
    mock = MagicMock()
    mock.check.return_value = HealthStatus(
        status="ok", store_ready=True, model_ready=True, index_size=42
    )
    return mock


@pytest.fixture
def client(monkeypatch, mock_health_use_cases):
    monkeypatch.setattr("api.main.bootstrap", lambda: None)
    monkeypatch.setattr("api.main.get_faiss_client", lambda: MagicMock(is_ready=False))

    app.dependency_overrides[get_health_use_cases] = lambda: mock_health_use_cases

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
