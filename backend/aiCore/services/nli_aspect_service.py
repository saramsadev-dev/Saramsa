"""
NLI-based aspect classification service using cross-encoder/nli-deberta-v3-small.

This service replaces cosine similarity-based aspect matching with Natural Language Inference (NLI)
classification to improve aspect assignment accuracy and reduce unmapped comments.
"""

import logging
import time
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SingletonMeta(type):
    """Metaclass for singleton pattern."""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class NliAspectService(metaclass=SingletonMeta):
    """
    Singleton service for NLI-based aspect classification.
    
    Uses cross-encoder/nli-deberta-v3-small to classify comments against aspects
    using zero-shot Natural Language Inference with hypothesis templates.
    """
    
    def __init__(self):
        """Initialize the NLI aspect classification service."""
        self.model = None
        self.model_name = "cross-encoder/nli-deberta-v3-small"
        self.batch_size = 64
        self.entailment_threshold = 0.7  # Higher threshold for more selective matching
        self._load_model()
    
    def _load_model(self):
        """Load the NLI cross-encoder model."""
        if self.model is not None:
            return
        
        logger.info(f"Loading NLI aspect model: {self.model_name}")
        start_time = time.time()
        
        try:
            # Lazy import to avoid startup issues
            from sentence_transformers import CrossEncoder
            
            self.model = CrossEncoder(self.model_name)
            load_time = time.time() - start_time
            logger.info(f"✅ NLI aspect model loaded successfully in {load_time:.2f}s")
        except Exception as e:
            logger.error(f"❌ Failed to load NLI aspect model: {e}")
            raise RuntimeError(f"Could not load NLI model {self.model_name}: {e}")
    
    def classify_aspects(self, comments: List[str], aspects: List[str]) -> List[Dict[str, Any]]:
        """
        Classify comments against aspects using NLI-based zero-shot classification.
        
        Args:
            comments: List of comment strings to classify
            aspects: List of aspect names to classify against
            
        Returns:
            List of classification results, one per comment:
            {
                "comment_id": int,
                "comment_text": str,
                "matched_aspects": List[str],
                "aspect_scores": Dict[str, float]
            }
        """
        if not comments or not aspects:
            logger.warning("Empty comments or aspects provided to classify_aspects")
            return []
        
        logger.info(f"Classifying {len(comments)} comments against {len(aspects)} aspects using NLI")
        start_time = time.time()
        
        # Prepare all (comment, hypothesis) pairs — sequential: all aspects for comment 0, then comment 1, etc.
        pairs = []
        for comment in comments:
            for aspect in aspects:
                pairs.append([comment, f"This feedback is about {aspect}."])
        
        logger.info(f"Created {len(pairs)} (comment, hypothesis) pairs for NLI classification")
        
        # Process in batches for efficiency
        all_scores = []
        num_batches = (len(pairs) + self.batch_size - 1) // self.batch_size
        
        for batch_idx in range(num_batches):
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(pairs))
            batch_pairs = pairs[start_idx:end_idx]
            
            batch_start = time.time()
            batch_scores = self.model.predict(batch_pairs)
            batch_time = time.time() - batch_start
            
            # Convert to list of floats to avoid numpy array issues
            # NLI models return [contradiction, neutral, entailment] logits
            # We want the entailment probability after softmax
            batch_scores_list = []
            for score in batch_scores:
                if hasattr(score, '__getitem__') and len(score) >= 3:
                    # Apply softmax to convert logits to probabilities
                    # Lazy import numpy to avoid startup issues
                    import numpy as np
                    logits = np.array(score)
                    exp_logits = np.exp(logits - np.max(logits))  # Numerical stability
                    probabilities = exp_logits / np.sum(exp_logits)
                    
                    # Take the entailment probability (index 2)
                    entailment_prob = float(probabilities[2])
                    batch_scores_list.append(entailment_prob)
                else:
                    # Fallback for unexpected format
                    try:
                        batch_scores_list.append(float(score))
                    except:
                        batch_scores_list.append(0.0)
            
            all_scores.extend(batch_scores_list)
            
            logger.debug(f"Batch {batch_idx + 1}/{num_batches}: {len(batch_pairs)} pairs processed in {batch_time:.3f}s")
        
        # Organize scores by comment (pairs are sequential: comment_0*all_aspects, comment_1*all_aspects, ...)
        num_aspects = len(aspects)
        results = []
        for comment_idx, comment in enumerate(comments):
            aspect_scores = {}
            base = comment_idx * num_aspects
            for aspect_idx, aspect in enumerate(aspects):
                aspect_scores[aspect] = all_scores[base + aspect_idx]
            
            # Determine matched aspects
            matched_aspects = []
            
            # First, check for aspects above threshold
            for aspect, score in aspect_scores.items():
                if score > self.entailment_threshold:
                    matched_aspects.append(aspect)
            
            # If no aspects above threshold, assign the highest-scoring aspect
            if not matched_aspects:
                best_aspect = max(aspect_scores.items(), key=lambda x: x[1])[0]
                matched_aspects = [best_aspect]
                logger.debug(f"Comment {comment_idx}: No aspects above threshold {self.entailment_threshold}, "
                           f"assigned best aspect '{best_aspect}' (score: {aspect_scores[best_aspect]:.3f})")
            
            results.append({
                "comment_id": comment_idx,
                "comment_text": comment,
                "matched_aspects": matched_aspects,
                "aspect_scores": aspect_scores
            })
        
        total_time = time.time() - start_time
        avg_time_per_comment = total_time / len(comments)
        
        # Calculate statistics
        total_matches = sum(len(r["matched_aspects"]) for r in results)
        multi_aspect_comments = sum(1 for r in results if len(r["matched_aspects"]) > 1)
        high_confidence_matches = sum(
            1 for r in results 
            for aspect in r["matched_aspects"] 
            if r["aspect_scores"][aspect] > self.entailment_threshold
        )
        
        logger.info(f"✅ NLI classification completed in {total_time:.2f}s ({avg_time_per_comment:.3f}s/comment)")
        logger.info(f"📊 Results: {total_matches} total matches, {multi_aspect_comments} multi-aspect comments")
        logger.info(f"📊 High confidence matches (>{self.entailment_threshold}): {high_confidence_matches}/{total_matches}")
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "model_type": "cross_encoder_nli",
            "batch_size": self.batch_size,
            "entailment_threshold": self.entailment_threshold,
            "loaded": self.model is not None
        }


# Global service instance
_nli_aspect_service = None


def get_nli_aspect_service() -> NliAspectService:
    """Get the global NLI aspect service instance."""
    global _nli_aspect_service
    if _nli_aspect_service is None:
        _nli_aspect_service = NliAspectService()
    return _nli_aspect_service