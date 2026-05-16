from typing import Optional

import httpx
from fastapi import HTTPException, Request, Response, status

from services.gateway.app.core.config import get_settings

settings = get_settings()

ROUTES = {
    "/api/v1/auth": settings.AUTH_SERVICE_URL,
    "/api/v1/products": settings.PRODUCTS_SERVICE_URL,
    "/api/v1/orders": settings.ORDERS_SERVICE_URL,
    "/api/v1/payment": settings.PAYMENT_SERVICE_URL,
    "/api/v1/notify": settings.NOTIFY_SERVICE_URL,
}

# Shared httpx client for efficient connection pooling
client = httpx.AsyncClient()


async def forward_request(request: Request, user_id: Optional[str] = None, role: Optional[str] = None) -> Response:
    """
    Forwards the incoming request to the appropriate microservice.
    """
    path = request.url.path
    matched_service_url = None
    for prefix, service_url in ROUTES.items():
        if path.startswith(prefix):
            matched_service_url = service_url
            break

    if not matched_service_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    target_url = httpx.URL(matched_service_url).join(path)

    headers = dict(request.headers)
    # Remove hop-by-hop headers and potentially conflicting headers
    # Host header is automatically set by httpx based on the target_url
    for h in ["host", "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade"]:
        headers.pop(h, None)
    
    if user_id:
        headers["X-User-ID"] = user_id
    if role:
        headers["X-User-Role"] = role

    try:
        req = client.build_request(
            method=request.method,
            url=target_url.copy_with(query=request.url.query),
            headers=headers,
            content=request.stream(),
            timeout=60.0 # Example timeout, adjust as needed
        )
        response = await client.send(req, stream=True)

        return Response(
            content=response.aiter_bytes(),
            status_code=response.status_code,
            headers=response.headers,
            media_type=response.headers.get("content-type"),
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Failed to connect to backend service: {exc}"
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code, detail=f"Backend service responded with an error: {exc.response.text}"
        )
