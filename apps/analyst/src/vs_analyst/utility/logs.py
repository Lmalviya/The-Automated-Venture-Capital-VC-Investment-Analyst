import logging
import sys
import structlog
from typing import Any

def setup_logging(log_level: str = "INFO") -> None:
    """
    Configures structlog for structured logging.
    If stderr is a terminal, it outputs colorized user-friendly logs.
    Otherwise, it outputs machine-readable JSON logs.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Check if stderr is a TTY (interactive terminal)
    if sys.stderr.isatty():
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )

# # Initialize logging when the module is imported
# setup_logging()

def get_logger(name: str = None) -> Any:
    """
    Returns a configured structlog logger.
    If `name` is provided, binds the logger name to the logging context.
    """
    if name:
        return structlog.get_logger().bind(logger_name=name)
    return structlog.get_logger()
