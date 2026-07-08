from typing import cast
from unittest.mock import MagicMock

import pytest

from api.infra.mistral import embeddings as embeddings_module
from api.infra.mistral.embeddings import MistralEmbedder


def _embedding_response(n: int, dimension: int = MistralEmbedder.DIMENSION) -> MagicMock:
    response = MagicMock()
    response.data = [MagicMock(embedding=[0.1] * dimension) for _ in range(n)]
    return response


def _embedder() -> MistralEmbedder:
    embedder = MistralEmbedder(api_key="test-key")
    embedder.client = MagicMock()
    return embedder


def test_embed_texts_happy_path():
    embedder = _embedder()
    mock_client = cast(MagicMock, embedder.client)
    mock_client.embeddings.create.return_value = _embedding_response(2)

    result = embedder.embed_texts(["un texte", "un autre texte"])

    assert len(result) == 2
    assert all(len(vec) == MistralEmbedder.DIMENSION for vec in result)
    mock_client.embeddings.create.assert_called_once_with(
        model="mistral-embed", inputs=["un texte", "un autre texte"]
    )


def test_embed_texts_filters_blank_entries():
    embedder = _embedder()
    mock_client = cast(MagicMock, embedder.client)
    mock_client.embeddings.create.return_value = _embedding_response(1)

    embedder.embed_texts(["  ", "un texte", ""])

    mock_client.embeddings.create.assert_called_once_with(
        model="mistral-embed", inputs=["un texte"]
    )


def test_embed_texts_raises_if_all_blank():
    embedder = _embedder()

    with pytest.raises(ValueError, match="No valid texts"):
        embedder.embed_texts(["", "   "])


def test_embed_texts_batches_by_batch_size():
    embedder = _embedder()
    mock_client = cast(MagicMock, embedder.client)
    embedder.batch_size = 2
    mock_client.embeddings.create.side_effect = [
        _embedding_response(2),
        _embedding_response(1),
    ]

    result = embedder.embed_texts(["a", "b", "c"])

    assert len(result) == 3
    assert mock_client.embeddings.create.call_count == 2


def test_client_constructed_with_native_retry_config(monkeypatch):
    mock_mistral_cls = MagicMock()
    monkeypatch.setattr(embeddings_module, "Mistral", mock_mistral_cls)

    MistralEmbedder(api_key="test-key")

    mock_mistral_cls.assert_called_once_with(
        api_key="test-key", retry_config=embeddings_module._RETRY_CONFIG
    )


def test_embed_texts_propagates_errors_from_client():
    embedder = _embedder()
    mock_client = cast(MagicMock, embedder.client)
    mock_client.embeddings.create.side_effect = Exception("500 Internal Server Error")

    with pytest.raises(Exception, match="500"):
        embedder.embed_texts(["un texte"])


def test_embed_texts_raises_if_no_data_returned():
    embedder = _embedder()
    mock_client = cast(MagicMock, embedder.client)
    response = MagicMock()
    response.data = []
    mock_client.embeddings.create.return_value = response

    with pytest.raises(RuntimeError, match="no embedding data"):
        embedder.embed_texts(["un texte"])


def test_embed_texts_raises_on_null_embedding():
    embedder = _embedder()
    mock_client = cast(MagicMock, embedder.client)
    response = MagicMock()
    response.data = [MagicMock(embedding=None)]
    mock_client.embeddings.create.return_value = response

    with pytest.raises(RuntimeError, match="null embedding"):
        embedder.embed_texts(["un texte"])


def test_embed_texts_raises_on_wrong_dimension():
    embedder = _embedder()
    mock_client = cast(MagicMock, embedder.client)
    response = MagicMock()
    response.data = [MagicMock(embedding=[0.1, 0.2])]
    mock_client.embeddings.create.return_value = response

    with pytest.raises(ValueError, match="Expected 1024-dim"):
        embedder.embed_texts(["un texte"])


def test_embed_query_returns_single_vector():
    embedder = _embedder()
    mock_client = cast(MagicMock, embedder.client)
    mock_client.embeddings.create.return_value = _embedding_response(1)

    result = embedder.embed_query("une question")

    assert len(result) == MistralEmbedder.DIMENSION
