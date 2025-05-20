import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime


class CustomJSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "extra"):
            log_record.update(record.extra)
        return json.dumps(log_record)


def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with both file and console handlers.

    Args:
        name (str): Name of the logger
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatters
    json_formatter = CustomJSONFormatter()
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler (JSON format)
    file_handler = RotatingFileHandler(
        log_dir / f"{name}.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    file_handler.setFormatter(json_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Create default logger instance
logger = setup_logger("lucie")
