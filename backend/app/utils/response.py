"""
Standardised API response helpers.
All endpoints return a consistent envelope:
  { "success": bool, "message": str, "data": Any, "meta": Any }
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
    meta: Optional[dict] = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "success": True,
        "message": message,
        "data": data,
    }
    if meta:
        body["meta"] = meta
    return JSONResponse(content=body, status_code=status_code)


def error_response(
    message: str,
    error_code: str = "ERROR",
    status_code: int = 400,
    details: Any = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "success": False,
        "error_code": error_code,
        "message": message,
    }
    if details is not None:
        body["details"] = details
    return JSONResponse(content=body, status_code=status_code)


def paginated_response(
    data: list,
    total: int,
    page: int,
    page_size: int,
    message: str = "Success",
) -> JSONResponse:
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    return success_response(
        data=data,
        message=message,
        meta={
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
    )
