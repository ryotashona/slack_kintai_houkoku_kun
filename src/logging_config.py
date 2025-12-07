import logging
import os
from typing import Optional

DEFAULT_LOG_LEVEL = "INFO"


def configure_logging(level: Optional[str] = None) -> None:
    """Configure application-wide logging."""
    log_level = level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
