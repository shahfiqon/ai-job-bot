"""Logging configuration using loguru."""
import sys
from loguru import logger

def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure loguru logger with the specified log level.
    
    Args:
        log_level: The log level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Remove default handler
    logger.remove()
    
    # Add custom handler with structured format
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )
    
    logger.info(f"Logging configured with level: {log_level}")

