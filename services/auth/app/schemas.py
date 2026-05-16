import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    """
    Pydantic model for user creation requests.
    """

    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """
    Pydantic model for user response data.
    """

    id: uuid.UUID
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """
    Pydantic model for JWT token responses.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """
    Pydantic model for refresh token requests.
    """

    refresh_token: str


class UserUpdate(BaseModel):
    """
    Pydantic model for updating user information.
    """

    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    """
    Pydantic model for login requests.
    """

    email: EmailStr
    password: str
