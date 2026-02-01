"""
Local Sentiment Service for Saramsa Local ML Pipeline

This service provides singleton-based sentiment classification using the 
cardiffnlp/twitter-roberta-base-sentiment-latest model from transformers. 
It supports both single text and batch processing with confidence scoring.

Key Features:
- Singleton pattern for model instance management
- cardiffnlp/twitter-roberta-base-sentiment-latest model
- Confidence level calculation (HIGH/MEDIUM/LOW/MIXED)
- Twitter-specific text preprocessing
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
        sentiment: Classified sentiment (POSITIVE, NEGATIVE, NEUTRAL, MIXED)
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
    Singleton service for sentiment classification using cardiffnlp/twitter-roberta-base-sentiment-latest.
    
    This service provides efficient sentiment analysis with confidence scoring
    and Twitter-specific text preprocessing capabilities.
    
    Model Specifications:
    - Model: cardiffnlp/twitter-roberta-base-sentiment-latest
    - Training: 124M tweets (Jan 2018 - Dec 2021) + TweetEval benchmark
    - Classes: 0=Negative, 1=Neutral, 2=Positive
    - Preprocessing: Handles @mentions and URLs appropriately
    """
    
    MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    
    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.5
    MEDIUM_CONFIDENCE_THRESHOLD = 0.25
    MIXED_SENTIMENT_THRESHOLD = 0.15
    
    # Batch processing constants
    DEFAULT_BATCH_SIZE = 32
    MAX_BATCH_SIZE = 64
    MIN_BATCH_SIZE = 8
    
    # Label mapping from model output to schema
    LABEL_MAPPING = {
        'positive': 'POSITIVE',
        'negative': 'NEGATIVE', 
        'neutral': 'NEUTRAL'
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
            
            # Set device preference (CPU for compatibility, GPU if available)
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
                return_all_scores=True,  # Get scores for all classes
                top_k=None  # Return all scores
            )
            
            # Test model with a simple classification
            test_result = self._pipeline("test")
            if not test_result or not isinstance(test_result, list):
                raise RuntimeError("Model test failed - unexpected output format")
            
            # With return_all_scores=True and top_k=None, we get a list of lists
            # Each inner list contains all class scores for one input
            first_result = test_result[0]
            
            if not isinstance(first_result, list) or len(first_result) < 3:
                raise RuntimeError("Model test failed - expected list of 3 sentiment classes")
            
            # Verify each result has label and score
            for result in first_result:
                if not isinstance(result, dict) or 'label' not in result or 'score' not in result:
                    logger.error(f"Invalid result format: {result}")
                    raise RuntimeError("Model test failed - invalid result format")
            
            logger.info(f"Model test passed. Sample result: {first_result[0]}")
            
            logger.info(
                f"Successfully loaded {self.MODEL_NAME} "
                f"(device: {device_name}, classes: {len(test_result[0])})"
            )
            
        except Exception as e:
            error_msg = f"Failed to load sentiment model {self.MODEL_NAME}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for Twitter-specific sentiment analysis.
        
        The cardiffnlp model was trained on Twitter data, so we apply
        Twitter-specific preprocessing to improve accuracy.
        
        Args:
            text: Raw input text
            
        Returns:
            Preprocessed text suitable for the model
        """
        if not text or not text.strip():
            return ""
        
        # Start with the original text
        processed_text = text.strip()
        
        # Handle @mentions - replace with @user (common Twitter preprocessing)
        processed_text = re.sub(r'@\w+', '@user', processed_text)
        
        # Handle URLs - replace with http (common Twitter preprocessing)
        processed_text = re.sub(r'http\S+|www\S+|https\S+', 'http', processed_text, flags=re.MULTILINE)
        
        # Normalize whitespace
        processed_text = re.sub(r'\s+', ' ', processed_text).strip()
        
        # Handle empty result
        if not processed_text:
            processed_text = "neutral text"  # Fallback for empty preprocessed text
        
        return processed_text
    
    def _calculate_confidence(self, scores: List[Dict[str, float]]) -> Tuple[str, str]:
        """
        Calculate confidence level and detect mixed sentiment based on probability scores.
        
        Args:
            scores: List of score dictionaries from the model (all classes)
            
        Returns:
            Tuple of (sentiment, confidence_level)
        """
        if not scores or len(scores) < 3:
            return "NEUTRAL", "LOW"
        
        # Extract probabilities and sort by score
        sorted_scores = sorted(scores, key=lambda x: x['score'], reverse=True)
        
        top_score = sorted_scores[0]
        second_score = sorted_scores[1]
        
        top_prob = top_score['score']
        second_prob = second_score['score']
        
        # Get the predicted sentiment
        predicted_label = top_score['label']
        sentiment = self.LABEL_MAPPING.get(predicted_label, 'NEUTRAL')
        
        # Calculate confidence difference
        confidence_diff = top_prob - second_prob
        
        # Check for mixed sentiment (top two probabilities are very close)
        if confidence_diff < self.MIXED_SENTIMENT_THRESHOLD:
            return "MIXED", "LOW"
        
        # Determine confidence level based on difference
        if confidence_diff > self.HIGH_CONFIDENCE_THRESHOLD:
            confidence = "HIGH"
        elif confidence_diff > self.MEDIUM_CONFIDENCE_THRESHOLD:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        return sentiment, confidence
    
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
            
            # Extract the scores for all classes
            scores = result[0]  # First (and only) result for single text
            if not isinstance(scores, list):
                raise RuntimeError("Expected list of scores for all classes")
            
            # Calculate sentiment and confidence
            sentiment, confidence = self._calculate_confidence(scores)
            
            # Create raw scores dictionary
            raw_scores = {
                self.LABEL_MAPPING.get(score['label'], score['label']): score['score']
                for score in scores
            }
            
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
                    # Process valid text result
                    scores = all_results[valid_result_idx]  # This is a list of score dicts
                    sentiment, confidence = self._calculate_confidence(scores)
                    
                    raw_scores = {
                        self.LABEL_MAPPING.get(score['label'], score['label']): score['score']
                        for score in scores
                    }
                    
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