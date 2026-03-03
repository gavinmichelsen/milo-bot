"""
Centralized logging configuration for Milo bot.

Provides a consistent logging format across all modules with
both console and file output.
"""

import logging
import sys


def setup_logger(name: str = "milo", level: int = logging.INFO) -> logging.Logger:
    """Create and configure a logger instance.

    Args:
        name: Logger name, typically the module name.
        level: Logging level (default: INFO).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)-12s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
