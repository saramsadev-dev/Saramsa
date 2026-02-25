"""
Local Sentiment Service for Saramsa Local ML Pipeline

This service provides singleton-based sentiment classification using the
nlptown/bert-base-multilingual-uncased-sentiment model from transformers.
It supports both single text and batch processing with confidence scoring.

Key Features:
- Singleton pattern for model instance management
- nlptown/bert-base-multilingual-uncased-sentiment model (trained on 629K product reviews)
- 5-star output mapped to 3-class sentiment (POSITIVE/NEGATIVE/NEUTRAL)
- Confidence level calculation (HIGH/MEDIUM/LOW)
- Batch processing support for efficiency
- Comprehensive error handling and logging
"""

import logging
import numpy as np
import re
from typing import List, Dict, Optional, Union, Tuple
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from threading import Lock
from dataclasses import dataclass
import time
import os

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """
    Data class for sentiment classification results.
    
    Attributes:
        sentiment: Classified sentiment (POSITIVE, NEGATIVE, NEUTRAL)
        confidence: Confidence level (HIGH, MEDIUM, LOW)
        raw_scores: Dictionary of raw probability scores for each class
        processing_time: Time taken for classification in seconds
    """
    sentiment: str
    confidence: str
    raw_scores: Dict[str, float]
    processing_time: float = 0.0


class SingletonMeta(type):
    """
    Metaclass that implements the Singleton pattern.
    Ensures only one instance of LocalSentimentService exists per process.
    """
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        """
        Thread-safe singleton implementation.
        """
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class LocalSentimentService(metaclass=SingletonMeta):
    """
    Singleton service for sentiment classification using nlptown/bert-base-multilingual-uncased-sentiment.

    This service provides efficient sentiment analysis with confidence scoring,
    optimized for customer feedback and product review text.

    Model Specifications:
    - Model: nlptown/bert-base-multilingual-uncased-sentiment
    - Training: 629K product reviews (English, German, French, Dutch, Italian, Spanish)
    - Classes: 5 stars (mapped to POSITIVE/NEGATIVE/NEUTRAL)
    - Accuracy: 95% off-by-1 on English product reviews
    """

    MODEL_NAME = "nlptown/bert-base-multilingual-uncased-sentiment"

    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.5
    MEDIUM_CONFIDENCE_THRESHOLD = 0.25
    MIXED_SENTIMENT_THRESHOLD = 0.15

    # Batch processing constants
    DEFAULT_BATCH_SIZE = 32
    MAX_BATCH_SIZE = 64
    MIN_BATCH_SIZE = 8

    # Star-to-sentiment mapping: 1-2 stars = NEGATIVE, 3 stars = NEUTRAL, 4-5 stars = POSITIVE
    STAR_TO_SENTIMENT = {
        '1 star': 'NEGATIVE',
        '2 stars': 'NEGATIVE',
        '3 stars': 'NEUTRAL',
        '4 stars': 'POSITIVE',
        '5 stars': 'POSITIVE',
    }

    # Label mapping for raw_scores output (collapsed to 3-class)
    LABEL_MAPPING = {
        'POSITIVE': 'POSITIVE',
        'NEGATIVE': 'NEGATIVE',
        'NEUTRAL': 'NEUTRAL',
    }
    
    def __init__(self):
        """
        Initialize the sentiment service with model loading and error handling.
        
        Raises:
            RuntimeError: If model loading fails
        """
        self._model = None
        self._tokenizer = None
        self._pipeline = None
        self._stats = {
            'classifications': 0,
            'batch_classifications': 0,
            'total_processing_time': 0.0,
            'last_classification_time': None
        }
        self._stats_lock: Lock = Lock()
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """
        Load the sentiment classification model with comprehensive error handling.

        Raises:
            RuntimeError: If model loading fails
        """
        try:
            logger.info(f"Loading sentiment model: {self.MODEL_NAME}")

            # Set device preference (GPU if available)
            device = 0 if torch.cuda.is_available() else -1
            device_name = "cuda" if device == 0 else "cpu"
            logger.info(f"Using device: {device_name}")

            # Load tokenizer and model
            self._tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
            model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME)

            # Create pipeline for efficient inference
            self._pipeline = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=self._tokenizer,
                device=device,
                top_k=None,  # Return all 5 star scores
            )

            # Test model with a simple classification
            test_result = self._pipeline("test")
            if not test_result or not isinstance(test_result, list):
                raise RuntimeError("Model test failed - unexpected output format")

            first_result = test_result[0]
            if not isinstance(first_result, list) or len(first_result) < 5:
                raise RuntimeError("Model test failed - expected list of 5 star classes")

            logger.info(f"Model test passed. Sample result: {first_result[0]}")
            logger.info(
                f"Successfully loaded {self.MODEL_NAME} "
                f"(device: {device_name}, classes: {len(first_result)})"
            )

        except Exception as e:
            error_msg = f"Failed to load sentiment model {self.MODEL_NAME}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for sentiment analysis.

        Minimal preprocessing — the nlptown model was trained on real product
        reviews and handles natural text well without heavy cleaning.

        Args:
            text: Raw input text

        Returns:
            Preprocessed text suitable for the model
        """
        if not text or not text.strip():
            return ""

        # Normalize whitespace
        processed_text = re.sub(r'\s+', ' ', text.strip())

        if not processed_text:
            processed_text = "neutral text"

        return processed_text
    
    def _collapse_star_scores(self, scores: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Collapse 5-star probabilities into 3-class sentiment probabilities.

        Mapping: 1-2 stars → NEGATIVE, 3 stars → NEUTRAL, 4-5 stars → POSITIVE
        """
        collapsed = {'POSITIVE': 0.0, 'NEGATIVE': 0.0, 'NEUTRAL': 0.0}
        for item in scores:
            label = item['label']
            score = item['score']
            sentiment = self.STAR_TO_SENTIMENT.get(label)
            if sentiment:
                collapsed[sentiment] += score
        return collapsed

    def _calculate_confidence(self, scores: List[Dict[str, float]]) -> Tuple[str, str]:
        """
        Calculate confidence level from 5-star scores collapsed to 3-class sentiment.

        Args:
            scores: List of score dictionaries from the model (5 star classes)

        Returns:
            Tuple of (sentiment, confidence_level)
        """
        if not scores or len(scores) < 5:
            return "NEUTRAL", "LOW"

        # Collapse 5 stars → 3 classes
        collapsed = self._collapse_star_scores(scores)

        # Find top and second sentiment
        sorted_sentiments = sorted(collapsed.items(), key=lambda x: x[1], reverse=True)
        top_sentiment, top_prob = sorted_sentiments[0]
        _, second_prob = sorted_sentiments[1]

        # Calculate confidence difference
        confidence_diff = top_prob - second_prob

        # When top two probabilities are very close, classify as NEUTRAL with LOW confidence
        if confidence_diff < self.MIXED_SENTIMENT_THRESHOLD:
            return "NEUTRAL", "LOW"

        # Determine confidence level based on difference
        if confidence_diff > self.HIGH_CONFIDENCE_THRESHOLD:
            confidence = "HIGH"
        elif confidence_diff > self.MEDIUM_CONFIDENCE_THRESHOLD:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return top_sentiment, confidence
    
    def classify_sentiment(self, text: str) -> SentimentResult:
        """
        Classify sentiment for a single text with confidence scoring.
        
        Args:
            text: Input text to classify
            
        Returns:
            SentimentResult containing classification and confidence information
            
        Raises:
            ValueError: If text is empty or None
            RuntimeError: If model is not initialized or classification fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty or None")
        
        if self._pipeline is None:
            raise RuntimeError("Sentiment model is not initialized")
        
        start_time = time.time()
        
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            # Classify sentiment
            result = self._pipeline(processed_text)
            
            if not result or not isinstance(result, list) or not result[0]:
                raise RuntimeError("Unexpected model output format")
            
            # Extract the scores for all classes (5 star ratings)
            scores = result[0]  # First (and only) result for single text
            if not isinstance(scores, list):
                raise RuntimeError("Expected list of scores for all classes")

            # Calculate sentiment and confidence
            sentiment, confidence = self._calculate_confidence(scores)

            # Create raw scores dictionary (collapsed to 3-class)
            raw_scores = self._collapse_star_scores(scores)
            
            processing_time = time.time() - start_time
            
            # Update statistics
            with self._stats_lock:
                self._stats['classifications'] += 1
                self._stats['total_processing_time'] += processing_time
                self._stats['last_classification_time'] = time.time()
            
            return SentimentResult(
                sentiment=sentiment,
                confidence=confidence,
                raw_scores=raw_scores,
                processing_time=processing_time
            )
            
        except Exception as e:
            error_msg = f"Failed to classify sentiment for text: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def classify_batch(self, texts: List[str]) -> List[SentimentResult]:
        """
        Classify sentiment for a batch of texts efficiently.
        
        Args:
            texts: List of input texts to classify
            
        Returns:
            List of SentimentResult objects for each input text
            
        Raises:
            ValueError: If texts list is empty
            RuntimeError: If model is not initialized or classification fails
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        if self._pipeline is None:
            raise RuntimeError("Sentiment model is not initialized")
        
        start_time = time.time()
        
        try:
            # Preprocess all texts
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # Filter out empty texts but keep track of indices
            valid_texts = []
            valid_indices = []
            for i, processed_text in enumerate(processed_texts):
                if processed_text:
                    valid_texts.append(processed_text)
                    valid_indices.append(i)
            
            if not valid_texts:
                raise ValueError("No valid texts found after preprocessing")
            
            logger.debug(f"Classifying sentiment for {len(valid_texts)} texts")
            
            # Determine batch size
            batch_size = min(
                self.DEFAULT_BATCH_SIZE,
                max(self.MIN_BATCH_SIZE, len(valid_texts))
            )
            
            # Override with environment variable if set
            env_batch_size = os.getenv('SENTIMENT_BATCH_SIZE')
            if env_batch_size:
                try:
                    batch_size = max(self.MIN_BATCH_SIZE, min(self.MAX_BATCH_SIZE, int(env_batch_size)))
                except ValueError:
                    logger.warning(f"Invalid SENTIMENT_BATCH_SIZE: {env_batch_size}")
            
            # Classify in batches
            all_results = []
            for i in range(0, len(valid_texts), batch_size):
                batch_texts = valid_texts[i:i + batch_size]
                batch_results = self._pipeline(batch_texts)
                all_results.extend(batch_results)
            
            # Process results
            results = []
            valid_result_idx = 0
            
            for i, original_text in enumerate(texts):
                if i in valid_indices:
                    # Process valid text result (5-star scores)
                    scores = all_results[valid_result_idx]
                    sentiment, confidence = self._calculate_confidence(scores)

                    # Collapse to 3-class for raw_scores
                    raw_scores = self._collapse_star_scores(scores)

                    results.append(SentimentResult(
                        sentiment=sentiment,
                        confidence=confidence,
                        raw_scores=raw_scores,
                        processing_time=0.0  # Individual timing not available in batch
                    ))
                    valid_result_idx += 1
                else:
                    # Handle empty/invalid text
                    results.append(SentimentResult(
                        sentiment="NEUTRAL",
                        confidence="LOW",
                        raw_scores={"POSITIVE": 0.33, "NEGATIVE": 0.33, "NEUTRAL": 0.34},
                        processing_time=0.0
                    ))
            
            total_processing_time = time.time() - start_time
            
            # Update statistics
            with self._stats_lock:
                self._stats['batch_classifications'] += 1
                self._stats['classifications'] += len(texts)
                self._stats['total_processing_time'] += total_processing_time
                self._stats['last_classification_time'] = time.time()
            
            logger.debug(f"Successfully classified {len(texts)} texts in {total_processing_time:.3f}s")
            return results
            
        except Exception as e:
            error_msg = f"Failed to classify batch sentiment: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def get_statistics(self) -> Dict[str, Union[int, float, None]]:
        """
        Get service usage statistics.
        
        Returns:
            Dictionary containing usage statistics
        """
        with self._stats_lock:
            avg_processing_time = (
                self._stats['total_processing_time'] / self._stats['classifications']
                if self._stats['classifications'] > 0 else 0.0
            )
            
            return {
                'total_classifications': self._stats['classifications'],
                'batch_operations': self._stats['batch_classifications'],
                'total_processing_time': self._stats['total_processing_time'],
                'average_processing_time': avg_processing_time,
                'last_classification_time': self._stats['last_classification_time'],
                'model_name': self.MODEL_NAME
            }
    
    def reset_statistics(self) -> None:
        """Reset service statistics."""
        with self._stats_lock:
            self._stats = {
                'classifications': 0,
                'batch_classifications': 0,
                'total_processing_time': 0.0,
                'last_classification_time': None
            }
    
    @property
    def is_initialized(self) -> bool:
        """
        Check if the sentiment model is properly initialized.
        
        Returns:
            True if model is loaded and ready, False otherwise
        """
        return self._pipeline is not None
    
    @property
    def model_info(self) -> Dict[str, Union[str, int, bool]]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary containing model metadata
        """
        device_info = "not_loaded"
        if self._pipeline and hasattr(self._pipeline, 'device'):
            device_info = str(self._pipeline.device)
        
        return {
            "model_name": self.MODEL_NAME,
            "device": device_info,
            "is_initialized": self.is_initialized,
            "supported_labels": list(self.LABEL_MAPPING.values()),
            "confidence_thresholds": {
                "high": self.HIGH_CONFIDENCE_THRESHOLD,
                "medium": self.MEDIUM_CONFIDENCE_THRESHOLD,
                "mixed": self.MIXED_SENTIMENT_THRESHOLD
            }
        }