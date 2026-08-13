# API-Gateway-Rate-Limiter-Analytics-
A high-performance API Gateway built with Python, featuring a Redis-based Rate Limiting engine, asynchronous request proxying, and background analytics processing.
This project demonstrates a production-ready approach to handling API traffic. It sits between clients and backend services, validating API keys, enforcing rate limits using the **Sliding Window algorithm**, and collecting request metrics asynchronously.

Tech Stack
 Framework: FastAPI (Python 3.12+)
 PostgreSQL (SQLAlchemy + Alembic)
 Caching & Rate Limiting: Redis + Lua Scripts
 HTTP Client: httpx (Async)
 Architecture: Layered Architecture / Domain-Driven Design (DDD)
 Infrastructure: Docker & Docker Compose
 Testing: Pytest

Architecture
 The project strictly follows **SOLID** principles and uses a **Layered Architecture**:
 API Layer: FastAPI routers and Dependency Injection.
 Service (Domain) Layer: Business logic (Rate Limiting, Proxying).
 Data Access Layer: Repository pattern for DB and Redis interactions.
