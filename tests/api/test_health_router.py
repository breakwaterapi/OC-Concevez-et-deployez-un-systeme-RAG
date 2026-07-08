def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["store_ready"] is True
    assert data["model_ready"] is True
    assert data["index_size"] == 42


def test_health_degraded(client, mock_health_use_cases):
    from api.modules.health.use_cases import HealthStatus

    mock_health_use_cases.check.return_value = HealthStatus(
        status="degraded", store_ready=False, model_ready=True, index_size=0
    )

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["store_ready"] is False