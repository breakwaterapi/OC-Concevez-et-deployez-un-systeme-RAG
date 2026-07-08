def test_metadata_returns_index_info(client):
    response = client.get("/metadata")

    assert response.status_code == 200
    data = response.json()
    assert data["region"] == "Île-de-France"
    assert data["n_events"] == 200
    assert data["n_chunks"] == 350
    assert data["embed_model"] == "mistral-embed"
    assert data["chat_model"] == "mistral-small-latest"
