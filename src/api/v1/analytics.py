import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.db.database import AsyncSessionLocal
from src.repositories.analytics import AnalyticsRepository
from src.services.analytics import ws_manager

router = APIRouter()


async def record_request_analytics_task(
    api_key_id: str,
    path: str,
    method: str,
    status_code: int,
    latency_ms: float,
):
    """
    Background Task for saving analytics in bd 
    and sending into WebSocket.
    """
    async with AsyncSessionLocal() as session:
        repo = AnalyticsRepository(session)
        await repo.log_request(
            api_key_id=api_key_id,
            path=path,
            method=method,
            status_code=status_code,
            latency_ms=latency_ms,
        )

    payload = {
        "event": "new_request",
        "api_key_id": str(api_key_id),
        "path": path,
        "method": method,
        "status_code": status_code,
        "latency_ms": round(latency_ms, 2),
        "timestamp": time.time(),
    }
    await ws_manager.broadcast(payload)


@router.websocket("/ws/analytics")
async def websocket_analytics_endpoint(websocket: WebSocket):
    """WebSocket endpoint for conecting dashboard."""
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
