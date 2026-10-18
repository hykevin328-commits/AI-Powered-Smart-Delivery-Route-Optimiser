"""
Structured logging configuration using structlog.
Supports both JSON (production) and human-readable console (development) output.
"""
from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from app.config.settings import settings


def setup_logging() -> None:
    """Configure structlog and stdlib logging."""

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # ── stdlib root logger ────────────────────────────────────────────────────
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # ── structlog processors ──────────────────────────────────────────────────
    # Note: add_logger_name is removed — it requires stdlib logger factory
    # and is incompatible with PrintLoggerFactory used here.
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.ExceptionRenderer(),
    ]

    if settings.LOG_FORMAT == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=False)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    return structlog.get_logger(name)
