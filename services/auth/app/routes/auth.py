from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, insert, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models import User, RefreshToken
from app.schemas import UserCreate, UserResponse, TokenResponse, RefreshRequest, LoginRequest

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
settings = get_settings()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_in: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Registers a new user in the system.
    """
    # Check if user with email already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    hashed_password = hash_password(user_in.password)

    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
    )
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(
    login_data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Authenticates a user and returns access and refresh tokens.
    """
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    refresh_token_expires_at = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    new_refresh_token_db = RefreshToken(
        user_id=user.id, token=refresh_token, expires_at=refresh_token_expires_at
    )
    db.add(new_refresh_token_db)
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_request: RefreshRequest, db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Refreshes an access token using a valid refresh token.
    """
    payload = decode_token(refresh_request.refresh_token)
    user_id_str: str | None = payload.get("sub")

    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if the refresh token exists in the database and is not revoked
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == refresh_request.refresh_token,
            RefreshToken.user_id == user_id_str,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow(),
        )
    )
    refresh_token_db = result.scalar_one_or_none()

    if not refresh_token_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch the user to ensure they are active
    user_result = await db.execute(select(User).where(User.id == refresh_token_db.user_id))
    user = user_result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with refresh token is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=new_access_token, refresh_token=refresh_request.refresh_token
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user(
    refresh_request: RefreshRequest, db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Revokes a refresh token, effectively logging out the user from that session.
    """
    payload = decode_token(refresh_request.refresh_token)
    user_id_str: str | None = payload.get("sub")

    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Find the refresh token in the database
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == refresh_request.refresh_token,
            RefreshToken.user_id == user_id_str,
            RefreshToken.is_revoked == False,
        )
    )
    refresh_token_db = result.scalar_one_or_none()

    if refresh_token_db:
        refresh_token_db.is_revoked = True
        await db.commit()
        return {"message": "Logout successful"}
    else:
        # Even if the token is not found or already revoked, we return 200 OK
        # to prevent leaking information about token existence.
        return {"message": "Logout successful"}
