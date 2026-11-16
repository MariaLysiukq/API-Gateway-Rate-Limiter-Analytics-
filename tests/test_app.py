from fastapi.testclient import TestClient

from src.main import app


def test_health_endpoint(patch_middleware_redis):
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_gateway_routes_are_registered():
    paths = app.openapi()["paths"]

    assert "/api/v1/proxy/{path}" in paths
    assert "/health" in paths


def test_analytics_websocket_accepts_connections(patch_middleware_redis):
    client = TestClient(app)

    with client.websocket_connect("/api/v1/ws/analytics") as websocket:
        websocket.send_text("ping")


def test_proxy_requires_api_key_header(patch_middleware_redis):
    client = TestClient(app)
    response = client.get("/api/v1/proxy/get")

    assert response.status_code == 422
