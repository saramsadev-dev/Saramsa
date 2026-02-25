"""
ML pipeline configuration constants.
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """Return a logger namespaced under the ml package."""
    return logging.getLogger(f"ml.{name}")


# Max comments to use for stratified sampling (e.g. for synthesis or reporting).
REPRESENTATIVE_COMMENTS_SAMPLE_SIZE = 25

# Target total processing time in seconds (performance SLA).
# Docstring target: 500–1,000 comments in ~25–30s.
TARGET_PROCESSING_TIME_SECONDS = 30
