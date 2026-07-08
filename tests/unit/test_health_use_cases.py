import pytest
from unittest.mock import MagicMock

from api.modules.health.use_cases import HealthStatus, HealthUseCases


def _make(store_ready=True, n_vectors=100, model_ready=True):
    store = MagicMock()
    store.is_ready = store_ready
    store.n_vectors = n_vectors
    model = MagicMock()
    model.is_ready.return_value = model_ready
    return HealthUseCases(store_checker=store, model_checker=model)


def test_check_both_ready():
    result = _make().check()

    assert isinstance(result, HealthStatus)
    assert result.status == "ok"
    assert result.store_ready is True
    assert result.model_ready is True
    assert result.index_size == 100


def test_check_store_not_ready():
    result = _make(store_ready=False, n_vectors=0).check()

    assert result.status == "degraded"
    assert result.store_ready is False
    assert result.model_ready is True
    assert result.index_size == 0


def test_check_model_not_ready():
    result = _make(model_ready=False).check()

    assert result.status == "degraded"
    assert result.model_ready is False


def test_check_both_not_ready():
    result = _make(store_ready=False, n_vectors=0, model_ready=False).check()

    assert result.status == "degraded"
    assert result.store_ready is False
    assert result.model_ready is False