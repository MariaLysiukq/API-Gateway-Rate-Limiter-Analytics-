from fastapi import APIRouter, Request, Depends, Response
from src.services.auth import verify_api_key
from src.services.proxy import ProxyService
from src.db.models import APIKey

router = APIRouter()
proxy_service = ProxyService()


@router.api_route(
    "/proxy/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    summary="Proxy requests to target service",
)
async def proxy_endpoint(
    path: str,
    request: Request,
    api_key: APIKey = Depends(verify_api_key),
):
    """Endpoint that requires API Key and proxy request on service."""
    status_code, headers, content = await proxy_service.forward_request(request, path)

    return Response(
        content=content,
        status_code=status_code,
        headers=headers,
    )
