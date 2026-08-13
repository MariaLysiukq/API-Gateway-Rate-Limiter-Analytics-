from typing import List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import RequestLog
from src.repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository[RequestLog]):

    def __init__(self, db_session: AsyncSession):
        super().__init__(RequestLog, db_session)

    async def log_request(
        self,
        api_key_id: Any,
        path: str,
        method: str,
        status_code: int,
        latency_ms: float,
    ) -> RequestLog:
        return await self.create(
            api_key_id=api_key_id,
            path=path,
            method=method,
            status_code=status_code,
            latency_ms=latency_ms,
        )

    async def get_summary_stats(self) -> Dict[str, Any]:
        query = select(
            func.count(RequestLog.id).label("total_requests"),
            func.avg(RequestLog.latency_ms).label("avg_latency_ms"),
        )
        result = await self.db.execute(query)
        stats = result.first()
        
        return {
            "total_requests": stats.total_requests if stats else 0,
            "avg_latency_ms": round(stats.avg_latency_ms, 2) if stats and stats.avg_latency_ms else 0.0,
        }
