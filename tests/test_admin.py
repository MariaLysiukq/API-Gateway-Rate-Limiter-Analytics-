import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import src.api.v1.gateway as gateway
from src.core.config import settings
from src.db.database import Base, get_db_session
from src.db.redis import get_redis
from src.main import app

ADMIN_TOKEN = "test-admin-token"
ADMIN_HEADERS = {"X-Admin-Token": ADMIN_TOKEN}


@pytest.fixture
def client(monkeypatch, patch_middleware_redis, fake_redis):
    """App wired to in-memory SQLite and Redis; the upstream service is faked."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(create_tables())
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_db_session():
        async with session_factory() as session:
            yield session

    async def override_redis():
        return fake_redis

    async def fake_forward_request(request, path):
        return 200, {"content-type": "application/json"}, b'{"upstream": "ok"}'

    async def skip_analytics(**kwargs):
        return None

    monkeypatch.setattr(settings, "ADMIN_TOKEN", ADMIN_TOKEN)
    monkeypatch.setattr(gateway.proxy_service, "forward_request", fake_forward_request)
    monkeypatch.setattr(gateway, "record_request_analytics_task", skip_analytics)
    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_redis] = override_redis

    yield TestClient(app)

    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


def create_key(client, **overrides):
    payload = {"email": "dev@example.com", "name": "dev", "rate_limit": 2, **overrides}
    response = client.post("/api/v1/admin/keys", json=payload, headers=ADMIN_HEADERS)
    assert response.status_code == 201, response.text
    return response.json()


def test_admin_requires_valid_token(client):
    assert client.get("/api/v1/admin/keys").status_code == 422
    response = client.get("/api/v1/admin/keys", headers={"X-Admin-Token": "wrong"})
    assert response.status_code == 401


def test_admin_disabled_without_configured_token(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_TOKEN", "")

    response = client.get("/api/v1/admin/keys", headers={"X-Admin-Token": "anything"})

    assert response.status_code == 503


def test_create_key_returns_raw_key_once_and_lists_without_it(client):
    created = create_key(client)

    assert created["api_key"].startswith("gw_")
    assert created["user_email"] == "dev@example.com"
    assert created["rate_limit"] == 2

    listed = client.get("/api/v1/admin/keys", headers=ADMIN_HEADERS).json()
    assert len(listed) == 1
    assert listed[0]["id"] == created["id"]
    assert "api_key" not in listed[0]


def test_same_email_reuses_user(client):
    create_key(client, name="first")
    create_key(client, name="second")

    listed = client.get("/api/v1/admin/keys", headers=ADMIN_HEADERS).json()

    assert {key["name"] for key in listed} == {"first", "second"}
    assert {key["user_email"] for key in listed} == {"dev@example.com"}


def test_create_key_validates_input(client):
    response = client.post(
        "/api/v1/admin/keys",
        json={"email": "not-an-email", "rate_limit": 0},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 422


def test_created_key_works_with_proxy_and_rate_limit(client):
    raw_key = create_key(client, rate_limit=2)["api_key"]
    headers = {"X-API-Key": raw_key}

    codes = [client.get("/api/v1/proxy/anything", headers=headers).status_code for _ in range(3)]

    assert codes == [200, 200, 429]


def test_revoked_key_is_rejected(client):
    created = create_key(client)
    headers = {"X-API-Key": created["api_key"]}
    assert client.get("/api/v1/proxy/anything", headers=headers).status_code == 200

    response = client.delete(f"/api/v1/admin/keys/{created['id']}", headers=ADMIN_HEADERS)

    assert response.status_code == 204
    assert client.get("/api/v1/proxy/anything", headers=headers).status_code == 401
    listed = client.get("/api/v1/admin/keys", headers=ADMIN_HEADERS).json()
    assert listed[0]["is_active"] is False


def test_revoke_unknown_key_returns_404(client):
    response = client.delete(
        "/api/v1/admin/keys/00000000-0000-0000-0000-000000000000",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 404
