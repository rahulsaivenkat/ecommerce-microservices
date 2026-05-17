from typing import Dict, Any

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.config import get_settings

PUBLIC_ROUTES = [
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/refresh"),
    ("POST", "/api/v1/payment/webhook"),
    ("GET", "/health"),
]


async def verify_jwt(request: Request, credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
    """
    Verifies the JWT token and extracts user information.
    """
    settings = get_settings()
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            token=credentials.credentials,
            key=settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_aud": False} # Audiences are not used here
        )
        user_id: str = payload.get("sub")
        role: str = payload.get("role")

        if user_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"user_id": user_id, "role": role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
