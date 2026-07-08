def test_ask_returns_answer(client):
    response = client.post("/ask", json={"question": "Quels concerts ce soir ?"})

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "Test ?"
    assert data["answer"] == "Réponse test."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["uid"] == "uid-1"
    assert "text" not in data["sources"][0]


def test_ask_empty_question_fails_validation(client):
    response = client.post("/ask", json={"question": ""})

    assert response.status_code == 422


def test_ask_question_too_long_fails_validation(client):
    response = client.post("/ask", json={"question": "x" * 501})

    assert response.status_code == 422


def test_ask_missing_question_fails_validation(client):
    response = client.post("/ask", json={})

    assert response.status_code == 422


def test_ask_whitespace_only_question_fails_validation(client):
    response = client.post("/ask", json={"question": "   "})

    assert response.status_code == 422


def test_ask_returns_503_when_index_not_ready(client, mock_rag_use_case):
    from api.common.exceptions import IndexNotReadyError

    mock_rag_use_case.execute.side_effect = IndexNotReadyError()

    response = client.post("/ask", json={"question": "Quels concerts ce soir ?"})

    assert response.status_code == 503
