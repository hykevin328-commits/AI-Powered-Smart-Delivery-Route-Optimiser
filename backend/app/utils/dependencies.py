"""
FastAPI shared dependencies for authentication and role-based access control.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import decode_token
from app.config.database import get_db
from app.utils.exceptions import ForbiddenException, UnauthorizedException

bearer_scheme = HTTPBearer(auto_error=False)


# ── Token extraction ──────────────────────────────────────────────────────────

async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> UUID:
    """Extract and validate JWT; return the authenticated user's UUID."""
    if not credentials:
        raise UnauthorizedException()
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Token payload missing 'sub'")
    return UUID(user_id)


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Return the full User ORM object for the authenticated user."""
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedException("User not found")
    if not user.is_active:
        raise ForbiddenException("Account is deactivated")
    return user


async def require_admin(current_user=Depends(get_current_user)):
    """Dependency that raises 403 unless the current user is an Admin."""
    from app.models.user import UserRole
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException("Admin access required")
    return current_user


async def require_delivery_partner(current_user=Depends(get_current_user)):
    """Allow both Admins and Delivery Partners."""
    from app.models.user import UserRole
    if current_user.role not in (UserRole.ADMIN, UserRole.DELIVERY_PARTNER):
        raise ForbiddenException("Delivery partner access required")
    return current_user


# ── Pagination ────────────────────────────────────────────────────────────────

class PaginationParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number"),
        page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
