"""Structured logging configuration using structlog."""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.core.config import get_settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to log entries."""
    settings = get_settings()
    event_dict.update(
        {
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        }
    )
    return event_dict


def drop_color_message_key(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Drop color message key for structured logging."""
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )

    # Configure structlog processors
    processors: list[Processor] = [
        # Add context
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        add_app_context,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Format output
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.log_format == "json":
        processors.extend([
            structlog.processors.JSONRenderer()
        ])
    else:
        processors.extend([
            drop_color_message_key,
            structlog.dev.ConsoleRenderer(colors=True),
        ])

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
