from typing import Optional
import httpx
from fastapi import HTTPException, Request, Response, status
from app.core.config import get_settings

settings = get_settings()

ROUTES = {
    "/api/v1/auth": settings.AUTH_SERVICE_URL,
    "/api/v1/products": settings.PRODUCTS_SERVICE_URL,
    "/api/v1/cart": settings.ORDERS_SERVICE_URL,
    "/api/v1/orders": settings.ORDERS_SERVICE_URL,
    "/api/v1/payment": settings.PAYMENT_SERVICE_URL,
    "/api/v1/notify": settings.NOTIFY_SERVICE_URL,
}

client = httpx.AsyncClient()

async def forward_request(request: Request, user_id: Optional[str] = None, role: Optional[str] = None) -> Response:
    path = request.url.path
    matched_service_url = None

    for prefix, service_url in ROUTES.items():
        if path.startswith(prefix):
            matched_service_url = service_url
            break

    if not matched_service_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    target_url = str(matched_service_url) + path

    headers = dict(request.headers)
    # Remove headers that should not be forwarded to the backend service
    for h in ["host", "connection", "keep-alive", "transfer-encoding"]:
        headers.pop(h, None)

    if user_id:
        headers["X-User-ID"] = user_id
    if role:
        headers["X-User-Role"] = role

    try:
        body = await request.body()
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=dict(request.query_params),
            timeout=60.0
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            media_type=response.headers.get("content-type")
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Failed to connect to backend service: {exc}")
