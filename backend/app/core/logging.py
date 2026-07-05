"""
Structured logging configuration.

Call `configure_logging()` once, at application/pipeline startup. Everywhere
else, get a logger with `structlog.get_logger(__name__)` and log with keyword
arguments (e.g. `logger.info("order_placed", ticker=ticker, order_id=oid)`)
rather than f-strings — this is what makes logs queryable later instead of
just readable.
"""

import logging
import sys

import structlog

from app.core.config import Environment, settings


def configure_logging() -> None:
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.environment == Environment.LOCAL:
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(settings.log_level)),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(stream=sys.stdout, level=settings.log_level)
