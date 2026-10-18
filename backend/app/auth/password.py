"""
Password hashing and verification using bcrypt via passlib.
"""
from __future__ import annotations

from passlib.context import CryptContext

# bcrypt is the only scheme; auto-upgrade deprecated hashes on verify
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Return bcrypt hash of the given plain-text password."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)
