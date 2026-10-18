"""
Authentication service – business logic for register, login,
refresh, logout, and profile management.
Keeps all DB interactions out of the router layer.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.auth.password import hash_password, verify_password
from app.config.settings import settings
from app.models.user import User, UserRole
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)
from app.utils.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    InvalidCredentialsException,
    InvalidTokenException,
    NotFoundException,
)
from app.utils.helpers import utcnow


class AuthService:

    # ── Register ──────────────────────────────────────────────────────────────

    async def register(self, db: AsyncSession, data: RegisterRequest) -> User:
        # Prevent duplicate emails
        existing = await db.execute(select(User).where(User.email == data.email.lower()))
        if existing.scalar_one_or_none():
            raise AlreadyExistsException("Email")

        user = User(
            full_name=data.full_name,
            email=data.email.lower(),
            phone=data.phone,
            hashed_password=hash_password(data.password),
            role=data.role,
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        await db.flush()  # get the PK before returning
        return user

    # ── Login ─────────────────────────────────────────────────────────────────

    async def login(self, db: AsyncSession, data: LoginRequest) -> Tuple[User, TokenResponse]:
        result = await db.execute(select(User).where(User.email == data.email.lower()))
        user: User | None = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsException()
        if not user.is_active:
            raise ForbiddenException("Account is deactivated. Please contact support.")

        tokens = self._issue_tokens(user)

        # Persist refresh token + last login timestamp
        user.refresh_token = tokens.refresh_token
        user.last_login_at = utcnow().isoformat()
        await db.flush()

        return user, tokens

    # ── Refresh ───────────────────────────────────────────────────────────────

    async def refresh(self, db: AsyncSession, refresh_token: str) -> TokenResponse:
        payload = decode_refresh_token(refresh_token)
        user_id = UUID(payload["sub"])

        result = await db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()

        if not user:
            raise InvalidTokenException()
        if user.refresh_token != refresh_token:
            # Token reuse detected – invalidate stored token (token rotation)
            user.refresh_token = None
            await db.flush()
            raise InvalidTokenException()
        if not user.is_active:
            raise ForbiddenException("Account is deactivated.")

        tokens = self._issue_tokens(user)
        user.refresh_token = tokens.refresh_token
        await db.flush()
        return tokens

    # ── Logout ────────────────────────────────────────────────────────────────

    async def logout(self, db: AsyncSession, user_id: UUID) -> None:
        result = await db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        if user:
            user.refresh_token = None
            await db.flush()

    # ── Profile ───────────────────────────────────────────────────────────────

    async def get_profile(self, db: AsyncSession, user_id: UUID) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User")
        return user

    async def update_profile(
        self, db: AsyncSession, user_id: UUID, data: UpdateProfileRequest
    ) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User")

        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        await db.flush()
        return user

    async def change_password(
        self, db: AsyncSession, user_id: UUID, data: ChangePasswordRequest
    ) -> None:
        result = await db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User")
        if not verify_password(data.current_password, user.hashed_password):
            raise InvalidCredentialsException()

        user.hashed_password = hash_password(data.new_password)
        user.refresh_token = None   # force re-login on all devices
        await db.flush()

    # ── Admin: list / deactivate users ───────────────────────────────────────

    async def deactivate_user(self, db: AsyncSession, user_id: UUID) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User")
        user.is_active = False
        user.refresh_token = None
        await db.flush()
        return user

    async def activate_user(self, db: AsyncSession, user_id: UUID) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User")
        user.is_active = True
        await db.flush()
        return user

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _issue_tokens(user: User) -> TokenResponse:
        access = create_access_token(user.id, user.role.value)
        refresh = create_refresh_token(user.id)
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


# Module-level singleton
auth_service = AuthService()
