# API Gateway with Rate Limiting and Analytics

[![Tests](https://github.com/MariaLysiukq/API-Gateway-Rate-Limiter-Analytics-/actions/workflows/tests.yml/badge.svg)](https://github.com/MariaLysiukq/API-Gateway-Rate-Limiter-Analytics-/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-rate%20limiting-DC382D?logo=redis&logoColor=white)

An async API gateway built with FastAPI. It sits between clients and a backend service, checks API keys, enforces rate limits in Redis, forwards requests with `httpx`, and records request metrics in the background.

## Features

- **API key authentication:** clients send `X-API-Key`; only a SHA-256 hash of each key is stored in PostgreSQL.
- **Admin API:** create, list and revoke API keys, protected by an admin token.
- **Two rate limiting layers:**
  - **Per API key, sliding window:** a Redis sorted set updated by an atomic Lua script. Each key has its own `rate_limit` (requests per minute).
  - **Per client IP, fixed window:** a global middleware that allows 100 requests per minute per IP using Redis `INCR`. If Redis is unavailable, it fails open.
- **Async proxy:** forwards `GET`, `POST`, `PUT`, `PATCH` and `DELETE` to `TARGET_SERVICE_URL` and strips hop-by-hop headers.
- **Background analytics:** each request is saved to `request_logs` (path, method, status, latency) and broadcast to WebSocket subscribers.
- **Rate limit headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `Retry-After` on `429`.

## Tech stack

FastAPI · SQLAlchemy 2 (async) + asyncpg · Alembic · Redis + Lua · httpx · Docker Compose · Pytest + fakeredis

## Architecture

```
Client ──X-API-Key──▶ IP rate limit middleware ──▶ /api/v1/proxy/{path}
                                                     │ 1. verify API key (PostgreSQL)
                                                     │ 2. sliding window check (Redis)
                                                     │ 3. forward request (httpx) ──▶ Target service
                                                     └ 4. background task: log + WebSocket broadcast
```

The code follows a layered structure:

```
src/
├── api/            # FastAPI routers and dependencies
├── core/           # settings (pydantic-settings)
├── db/             # SQLAlchemy models, async session, Redis client
├── middleware/     # global per-IP rate limiting
├── repositories/   # data access (repository pattern)
├── schemas/        # Pydantic request/response models
└── services/       # auth, proxy, analytics, rate limiter algorithms
```

## Getting started

Requirements: Docker and Docker Compose.

```bash
git clone https://github.com/MariaLysiukq/API-Gateway-Rate-Limiter-Analytics-.git
cd API-Gateway-Rate-Limiter-Analytics-
cp .env.example .env
docker compose up --build -d
docker compose exec app alembic upgrade head
```

The API docs are available at http://localhost:8000/docs.

### Create an API key

Set `ADMIN_TOKEN` in `.env` (the admin API is disabled while it is empty), then create a key. The owner is created automatically if the email is new:

```bash
curl -X POST http://localhost:8000/api/v1/admin/keys \
  -H "X-Admin-Token: change-me" \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "name": "demo", "rate_limit": 5}'
```

The response contains the raw key in `api_key`. It is shown only once; the gateway stores only its SHA-256 hash.

### Send requests through the gateway

```bash
curl -H "X-API-Key: <api_key from the response>" http://localhost:8000/api/v1/proxy/get
```

With `rate_limit = 5`, the sixth request within a minute returns `429 Too Many Requests`.

### Watch live analytics

Connect a WebSocket client to `ws://localhost:8000/api/v1/ws/analytics` to receive an event for every proxied request.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `ANY` | `/api/v1/proxy/{path}` | Authenticated, rate-limited proxy to `TARGET_SERVICE_URL` |
| `WS` | `/api/v1/ws/analytics` | Live stream of request events |
| `POST` | `/api/v1/admin/keys` | Create an API key (admin) |
| `GET` | `/api/v1/admin/keys` | List API keys (admin) |
| `DELETE` | `/api/v1/admin/keys/{id}` | Revoke an API key (admin) |

Admin endpoints require the `X-Admin-Token` header.

## Running tests

The tests use an in-memory Redis (`fakeredis`) and SQLite, so no running services are needed:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

## Possible improvements

- Aggregated analytics endpoint built on `AnalyticsRepository.get_summary_stats`
- Configurable IP limit through settings

## License

[MIT](LICENSE)
