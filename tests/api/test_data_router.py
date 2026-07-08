import httpx
import requests

from mistralai.models import MistralError


def test_rebuild_returns_200(client, mock_data_use_cases):
    response = client.post("/rebuild")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["n_chunks"] == 10
    assert data["n_parent_docs"] == 3
    mock_data_use_cases.prepare.execute.assert_called_once()
    mock_data_use_cases.build_index.execute.assert_called_once()


def test_rebuild_returns_503_on_openagenda_failure(client, mock_data_use_cases):
    mock_data_use_cases.prepare.execute.side_effect = requests.ConnectionError("unreachable")

    response = client.post("/rebuild")

    assert response.status_code == 503
    assert response.headers["retry-after"] == "60"
    assert "Open Agenda" in response.json()["detail"]
    mock_data_use_cases.build_index.execute.assert_not_called()


def test_rebuild_returns_503_on_mistral_failure(client, mock_data_use_cases):
    fake_response = httpx.Response(
        status_code=429, request=httpx.Request("POST", "https://api.mistral.ai/v1/embeddings")
    )
    mock_data_use_cases.build_index.execute.side_effect = MistralError(
        "quota exceeded", fake_response
    )

    response = client.post("/rebuild")

    assert response.status_code == 503
    assert response.headers["retry-after"] == "60"
    assert "Mistral" in response.json()["detail"]