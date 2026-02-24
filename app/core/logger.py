import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

from app.core.settings import settings


from contextvars import ContextVar

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Context variable to store the request ID
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="-")

class RequestIdFilter(logging.Filter):
    """Injects request_id from contextvars into log records."""
    def filter(self, record):
        req_id = request_id_ctx_var.get()
        if req_id != "-":
            # Prefix the actual message so RichHandler prints it on the console
            record.msg = f"[{req_id}] {record.msg}"
        return True

# Define log format for files
FILE_LOG_FORMAT = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
)

def setup_logger() -> logging.Logger:
    """Configure and return the application logger."""
    
    # Determine log level based on environment (you can add a setting for this)
    # Default to INFO, but allow overriding via environment variables if added later
    log_level = logging.INFO
    
    # Configure the root logger
    logging.basicConfig(
        level=log_level,
        format="%(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                markup=True,
                show_time=True,
                show_level=True,
                show_path=False # We handle path in the format
            )
        ],
    )

    logger = logging.getLogger("chief_webhooks")
    logger.addFilter(RequestIdFilter())

    # Add Rotating File Handler (10MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(
        LOGS_DIR / "app.log", maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(FILE_LOG_FORMAT)
    file_handler.setLevel(log_level)
    
    # Avoid adding multiple handlers if setup_logger is called multiple times
    if not logger.handlers:
        logger.addHandler(file_handler)

    # Set third-party loggers to WARNING to avoid noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)

    return logger

# Create a global logger instance to be imported across the app
logger = setup_logger()
