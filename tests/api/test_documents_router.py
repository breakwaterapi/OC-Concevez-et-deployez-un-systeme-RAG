def test_list_documents_default(client):
    response = client.get("/documents")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["uid"] == "uid-1"
    assert data[1]["uid"] == "uid-2"


def test_list_documents_limit(client):
    response = client.get("/documents", params={"limit": 1})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["uid"] == "uid-1"


def test_list_documents_offset(client):
    response = client.get("/documents", params={"offset": 1})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["uid"] == "uid-2"


def test_list_documents_limit_and_offset(client):
    response = client.get("/documents", params={"limit": 1, "offset": 1})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["uid"] == "uid-2"


def test_list_documents_invalid_limit(client):
    response = client.get("/documents", params={"limit": 0})

    assert response.status_code == 422


def test_get_document_found(client):
    response = client.get("/documents/uid-1")

    assert response.status_code == 200
    data = response.json()
    assert data["uid"] == "uid-1"
    assert data["text"] == "Texte source."


def test_get_document_not_found(client):
    response = client.get("/documents/unknown-uid")

    assert response.status_code == 404


def test_retrieve_returns_sources(client):
    response = client.get("/retrieve", params={"q": "concert jazz", "k": 3})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["uid"] == "uid-1"


def test_retrieve_missing_query_fails_validation(client):
    response = client.get("/retrieve")

    assert response.status_code == 422


def test_retrieve_empty_query_fails_validation(client):
    response = client.get("/retrieve", params={"q": ""})

    assert response.status_code == 422


def test_retrieve_whitespace_only_query_fails_validation(client):
    response = client.get("/retrieve", params={"q": "   "})

    assert response.status_code == 422


def test_retrieve_invalid_k_fails_validation(client):
    response = client.get("/retrieve", params={"q": "concert jazz", "k": 0})

    assert response.status_code == 422


def test_retrieve_returns_503_when_index_not_ready(client, mock_documents_use_case):
    from api.common.exceptions import IndexNotReadyError

    mock_documents_use_case.retrieve.side_effect = IndexNotReadyError()

    response = client.get("/retrieve", params={"q": "concert jazz"})

    assert response.status_code == 503
