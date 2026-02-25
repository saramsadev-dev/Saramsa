"""
Aspect Service Factory

Selects between zero-shot NLI and cosine-similarity aspect classification
based on the ASPECT_METHOD environment variable.

  ASPECT_METHOD=nli        -> ZeroShotAspectService  (default)
  ASPECT_METHOD=similarity -> SimilarityAspectService
"""

import os
import logging

logger = logging.getLogger(__name__)


def get_aspect_service():
    """Return the configured aspect classification service singleton."""
    method = os.getenv("ASPECT_METHOD", "nli").strip().lower()

    if method == "similarity":
        logger.info("Using cosine-similarity aspect classification (ASPECT_METHOD=similarity)")
        from aiCore.services.similarity_aspect_service import get_similarity_aspect_service
        return get_similarity_aspect_service()
    else:
        logger.info("Using zero-shot NLI aspect classification (ASPECT_METHOD=nli)")
        from aiCore.services.zero_shot_aspect_service import get_zero_shot_aspect_service
        return get_zero_shot_aspect_service()
