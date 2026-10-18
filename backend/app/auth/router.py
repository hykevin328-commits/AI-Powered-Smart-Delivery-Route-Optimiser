"""
Authentication API routes.

POST /auth/register          – create new account
POST /auth/login             – obtain access + refresh tokens
POST /auth/refresh           – exchange refresh token for new token pair
POST /auth/logout            – invalidate refresh token
GET  /auth/me                – get own profile
PUT  /auth/me                – update own profile
POST /auth/me/change-password
GET  /auth/users             – Admin: list all users
PUT  /auth/users/{id}/deactivate  – Admin only
PUT  /auth/users/{id}/activate    – Admin only
"""
from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import auth_service
from app.config.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)
from app.utils.dependencies import (
    PaginationParams,
    get_current_user,
    require_admin,
)
from app.utils.response import paginated_response, success_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Register ──────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await auth_service.register(db, data)
    return success_response(
        data=UserProfileResponse.model_validate(user).model_dump(),
        message="Account created successfully",
        status_code=201,
    )


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", summary="Login and receive JWT tokens")
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    user, tokens = await auth_service.login(db, data)
    return success_response(
        data={
            "tokens": tokens.model_dump(),
            "user": UserProfileResponse.model_validate(user).model_dump(),
        },
        message="Login successful",
    )


# ── Refresh ───────────────────────────────────────────────────────────────────

@router.post("/refresh", summary="Refresh access token")
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    tokens = await auth_service.refresh(db, data.refresh_token)
    return success_response(data=tokens.model_dump(), message="Token refreshed")


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout", summary="Logout and invalidate refresh token")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await auth_service.logout(db, current_user.id)
    return success_response(message="Logged out successfully")


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/me", summary="Get current user profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return success_response(
        data=UserProfileResponse.model_validate(current_user).model_dump()
    )


@router.put("/me", summary="Update current user profile")
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updated = await auth_service.update_profile(db, current_user.id, data)
    return success_response(
        data=UserProfileResponse.model_validate(updated).model_dump(),
        message="Profile updated",
    )


@router.post("/me/change-password", summary="Change account password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await auth_service.change_password(db, current_user.id, data)
    return success_response(message="Password changed. Please log in again.")


# ── Admin: User management ────────────────────────────────────────────────────

@router.get("/users", summary="[Admin] List all users")
async def list_users(
    pagination: PaginationParams = Depends(),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.utils.pagination import paginate

    query = select(User).order_by(User.created_at.desc())
    users, total = await paginate(db, query, pagination.page, pagination.page_size)
    return paginated_response(
        data=[UserProfileResponse.model_validate(u).model_dump() for u in users],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/users/{user_id}", summary="[Admin] Get user by ID")
async def get_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await auth_service.get_profile(db, user_id)
    return success_response(data=UserProfileResponse.model_validate(user).model_dump())


@router.put("/users/{user_id}/deactivate", summary="[Admin] Deactivate user")
async def deactivate_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await auth_service.deactivate_user(db, user_id)
    return success_response(
        data=UserProfileResponse.model_validate(user).model_dump(),
        message="User deactivated",
    )


@router.put("/users/{user_id}/activate", summary="[Admin] Activate user")
async def activate_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await auth_service.activate_user(db, user_id)
    return success_response(
        data=UserProfileResponse.model_validate(user).model_dump(),
        message="User activated",
    )
