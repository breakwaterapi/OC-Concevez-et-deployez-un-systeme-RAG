def test_rebuild_returns_200(client, mock_data_use_cases):
    response = client.post("/rebuild")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["n_chunks"] == 10
    assert data["n_parent_docs"] == 3
    mock_data_use_cases.prepare.execute.assert_called_once()
    mock_data_use_cases.build_index.execute.assert_called_once()