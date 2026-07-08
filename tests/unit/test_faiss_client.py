import tempfile

import pytest

from api.infra.faiss.store import FAISSClient

DIM = 4


def _embed_texts(texts):
    return [[float(i % DIM) * 0.1 + 0.01] * DIM for i, _ in enumerate(texts)]


def _embed_query(text):
    return [0.1] * DIM


@pytest.fixture
def client():
    return FAISSClient(embed_texts_fn=_embed_texts, embed_query_fn=_embed_query)


def test_initial_state_not_ready(client):
    assert client.is_ready is False
    assert client.n_vectors == 0
    assert client.n_parent_docs == 0
    assert client.get_parent_doc("any") is None
    assert client.list_parent_docs() == []


def test_build_sets_ready(client):
    texts = ["chunk A", "chunk B", "chunk C"]
    embeddings = _embed_texts(texts)
    metadatas = [{"uid": "ev-A"}, {"uid": "ev-A"}, {"uid": "ev-B"}]
    parent_docs = {"ev-A": "Full text A", "ev-B": "Full text B"}

    client.build(texts, embeddings, metadatas, parent_docs)

    assert client.is_ready is True
    assert client.n_vectors == 3
    assert client.n_parent_docs == 2


def test_build_stores_parent_docs(client):
    client.build(
        ["t1"], _embed_texts(["t1"]), [{"uid": "ev-X"}], {"ev-X": "Texte X"}
    )

    assert client.get_parent_doc("ev-X") == "Texte X"
    assert client.get_parent_doc("unknown") is None


def test_list_parent_docs(client):
    parent_docs = {"ev-A": "Texte A", "ev-B": "Texte B"}
    client.build(
        ["t1", "t2"],
        _embed_texts(["t1", "t2"]),
        [{"uid": "ev-A"}, {"uid": "ev-B"}],
        parent_docs,
    )

    result = dict(client.list_parent_docs())

    assert result == parent_docs


def test_search_raises_when_not_ready(client):
    with pytest.raises(RuntimeError, match="Index not loaded"):
        client.search("test query", k=3)


def test_search_parent_docs_dedupes_by_uid(client):
    texts = ["chunk A1", "chunk A2", "chunk B1"]
    embeddings = _embed_texts(texts)
    metadatas = [{"uid": "ev-A"}, {"uid": "ev-A"}, {"uid": "ev-B"}]
    parent_docs = {"ev-A": "Full text A", "ev-B": "Full text B"}
    client.build(texts, embeddings, metadatas, parent_docs)

    results = client.search_parent_docs("query", k=3)

    assert dict(results) == parent_docs
    assert len(results) == 2


def test_search_parent_docs_raises_when_not_ready(client):
    with pytest.raises(RuntimeError, match="Index not loaded"):
        client.search_parent_docs("test query", k=3)


def test_save_raises_when_not_built(client):
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(RuntimeError, match="No index to save"):
            client.save(tmp)


def test_load_raises_when_no_index(client):
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(FileNotFoundError):
            client.load(tmp)


def test_save_and_load_round_trip(client):
    texts = ["chunk A", "chunk B"]
    embeddings = _embed_texts(texts)
    metadatas = [{"uid": "ev-A"}, {"uid": "ev-B"}]
    parent_docs = {"ev-A": "Doc A", "ev-B": "Doc B"}

    client.build(texts, embeddings, metadatas, parent_docs)

    with tempfile.TemporaryDirectory() as tmp:
        client.save(tmp)

        fresh = FAISSClient(embed_texts_fn=_embed_texts, embed_query_fn=_embed_query)
        fresh.load(tmp)

        assert fresh.is_ready is True
        assert fresh.n_vectors == 2
        assert fresh.n_parent_docs == 2
        assert fresh.get_parent_doc("ev-A") == "Doc A"
        assert fresh.get_parent_doc("ev-B") == "Doc B"