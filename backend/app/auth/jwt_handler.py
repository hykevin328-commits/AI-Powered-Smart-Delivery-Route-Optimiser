"""
JWT token creation and decoding.

Token types
-----------
access  – short-lived (30 min default), carries user id + role
refresh – long-lived (7 days default), carries user id only, used to
          issue new access tokens without re-login
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from jose import JWTError, jwt

from app.config.settings import settings
from app.utils.exceptions import InvalidTokenException, TokenExpiredException


# ── Token creation ────────────────────────────────────────────────────────────

def _create_token(
    subject: str,
    token_type: str,
    extra_claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=15))
    payload: Dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: UUID, role: str) -> str:
    """Create a short-lived access JWT."""
    return _create_token(
        subject=str(user_id),
        token_type="access",
        extra_claims={"role": role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: UUID) -> str:
    """Create a long-lived refresh JWT."""
    return _create_token(
        subject=str(user_id),
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


# ── Token decoding ────────────────────────────────────────────────────────────

def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """
    Decode and validate a JWT.

    Raises:
        TokenExpiredException  – if the token is past its expiry
        InvalidTokenException  – if the token is malformed or wrong type
    """
    try:
        payload: Dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError as exc:
        if "expired" in str(exc).lower():
            raise TokenExpiredException()
        raise InvalidTokenException()

    if payload.get("type") != expected_type:
        raise InvalidTokenException()

    return payload


def decode_refresh_token(token: str) -> Dict[str, Any]:
    return decode_token(token, expected_type="refresh")
