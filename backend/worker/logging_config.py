#!/usr/bin/env python3
"""
Centralized logging configuration for workers.
"""

import logging
import os


def configure_logging(default_level: int | None = None) -> None:
    """Configure root logging if not already configured."""
    if logging.getLogger().handlers:
        return
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    if default_level is not None:
        level = default_level
    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s'
    )


