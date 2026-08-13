from typing import Tuple, Dict, Any
import httpx
from fastapi import Request
from src.core.config import settings


class ProxyService:
    
    HOP_BY_HOP_HEADERS = {
        "host",
        "content-length",
        "transfer-encoding",
        "connection",
        "keep-alive",
        "x-api-key",  # Видаляємо наш внутрішній заголовок перед відправкою далі
    }

    def __init__(self, target_base_url: str = settings.TARGET_SERVICE_URL):
        self.target_base_url = target_base_url

    def _clean_headers(self, headers: httpx.Headers) -> Dict[str, str]:
        """(Hop-by-hop)."""
        return {
            key: value
            for key, value in headers.items()
            if key.lower() not in self.HOP_BY_HOP_HEADERS
        }

    async def forward_request(
        self, request: Request, path: str
    ) -> Tuple[int, Dict[str, Any], bytes]:
        target_url = f"{self.target_base_url}/{path}"
        headers = self._clean_headers(request.headers)
        body = await request.body()

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=body,
            )

            res_headers = self._clean_headers(response.headers)
            return response.status_code, res_headers, response.content
