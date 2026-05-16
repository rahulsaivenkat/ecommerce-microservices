from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

import httpx
from fastapi import FastAPI, Request, Response, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from services.gateway.app.core.auth_middleware import verify_jwt, PUBLIC_ROUTES
from services.gateway.app.routes.proxy import forward_request, client as proxy_client # Import the shared client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the httpx client for proxying
    app.state.client = proxy_client
    yield
    # Close the httpx client when the app shuts down
    await app.state.client.aclose()


app = FastAPI(title="Gateway Service", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize HTTPBearer for authentication, but don't auto_error to handle manually
oauth2_scheme = HTTPBearer(auto_error=False)


@app.get("/health")
async def health_check():
    """
    Health check endpoint for the Gateway Service.
    """
    return {"status": "ok", "service": "gateway"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def catch_all(
    request: Request,
    path: str, # path:path takes the rest of the path, including possible subpaths
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme)
) -> Response:
    """
    Catch-all route to proxy requests to appropriate microservices.
    Handles authentication for non-public routes.
    """
    method = request.method
    request_path = request.url.path

    is_public_route = (method, request_path) in PUBLIC_ROUTES

    user_id: Optional[str] = None
    role: Optional[str] = None

    if not is_public_route:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        auth_data: Dict[str, Any] = await verify_jwt(request, credentials)
        user_id = auth_data["user_id"]
        role = auth_data["role"]

    return await forward_request(request, user_id=user_id, role=role)
