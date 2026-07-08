from unittest.mock import MagicMock

from api.modules.metadata.use_cases import IndexMetadata, MetadataUseCases


def _make(n_vectors=350, n_parent_docs=200):
    index_info = MagicMock()
    index_info.n_vectors = n_vectors
    index_info.n_parent_docs = n_parent_docs
    return MetadataUseCases(
        index_info=index_info,
        region="Île-de-France",
        date_from="2025-06-01T00:00:00Z",
        date_to="2027-06-01T00:00:00Z",
        embed_model="mistral-embed",
        chat_model="mistral-small-latest",
    )


def test_get_returns_index_metadata():
    result = _make().get()

    assert isinstance(result, IndexMetadata)
    assert result.region == "Île-de-France"
    assert result.date_from == "2025-06-01T00:00:00Z"
    assert result.date_to == "2027-06-01T00:00:00Z"
    assert result.n_events == 200
    assert result.n_chunks == 350
    assert result.embed_model == "mistral-embed"
    assert result.chat_model == "mistral-small-latest"
