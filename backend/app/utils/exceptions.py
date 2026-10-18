"""
Centralised application exception hierarchy.
Each exception maps to an HTTP status code and a machine-readable error code.
"""
from __future__ import annotations

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base for all application-level exceptions."""

    def __init__(self, status_code: int, detail: str, error_code: str = "APP_ERROR"):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


# ── Auth ──────────────────────────────────────────────────────────────────────

class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, "UNAUTHORIZED")


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status.HTTP_403_FORBIDDEN, detail, "FORBIDDEN")


class InvalidCredentialsException(AppException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Invalid email or password", "INVALID_CREDENTIALS")


class TokenExpiredException(AppException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Token has expired", "TOKEN_EXPIRED")


class InvalidTokenException(AppException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Invalid token", "INVALID_TOKEN")


# ── Resource ──────────────────────────────────────────────────────────────────

class NotFoundException(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(status.HTTP_404_NOT_FOUND, f"{resource} not found", "NOT_FOUND")


class AlreadyExistsException(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(status.HTTP_409_CONFLICT, f"{resource} already exists", "ALREADY_EXISTS")


class ValidationException(AppException):
    def __init__(self, detail: str):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, detail, "VALIDATION_ERROR")


# ── Business Logic ────────────────────────────────────────────────────────────

class OptimizationException(AppException):
    def __init__(self, detail: str = "Route optimization failed"):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail, "OPTIMIZATION_ERROR")


class GeocodingException(AppException):
    def __init__(self, detail: str = "Geocoding request failed"):
        super().__init__(status.HTTP_502_BAD_GATEWAY, detail, "GEOCODING_ERROR")


class ExternalAPIException(AppException):
    def __init__(self, service: str, detail: str = "External API request failed"):
        super().__init__(status.HTTP_502_BAD_GATEWAY, f"{service}: {detail}", "EXTERNAL_API_ERROR")


class OrderAlreadyAssignedException(AppException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, "Order is already assigned to a delivery partner", "ORDER_ALREADY_ASSIGNED")


class OrderAlreadyCompletedException(AppException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, "Order is already completed", "ORDER_ALREADY_COMPLETED")
