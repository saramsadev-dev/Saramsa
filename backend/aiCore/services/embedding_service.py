"""
Embedding Service for Saramsa Local ML Pipeline

This service provides singleton-based text embedding generation using the 
all-MiniLM-L6-v2 model from sentence-transformers. It supports both single 
text and batch processing with memory-efficient operations.

Key Features:
- Singleton pattern for model instance management
- all-MiniLM-L6-v2 model (384-dimensional embeddings)
- Batch processing support for efficiency
- Aspect embedding caching per processing run
- Comprehensive error handling and logging
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Union
from sentence_transformers import SentenceTransformer
import torch
from threading import Lock
import time
import os
import psutil

logger = logging.getLogger(__name__)


class SingletonMeta(type):
    """
    Metaclass that implements the Singleton pattern.
    Ensures only one instance of EmbeddingService exists per process.
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


class EmbeddingService(metaclass=SingletonMeta):
    """
    Singleton service for generating text embeddings using all-MiniLM-L6-v2.
    
    This service provides efficient text-to-vector conversion with caching
    capabilities for aspect embeddings during processing runs.
    
    Model Specifications:
    - Model: sentence-transformers/all-MiniLM-L6-v2
    - Parameters: 22.7M
    - Output Dimensions: 384
    - Training: 1B+ sentence pairs with contrastive learning
    """
    
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384
    
    # Batch processing optimization constants
    DEFAULT_BATCH_SIZE = 32
    MAX_BATCH_SIZE = 128
    MIN_BATCH_SIZE = 8
    MEMORY_THRESHOLD_MB = 1024  # 1GB memory threshold for batch size adjustment
    
    def __init__(self):
        """
        Initialize the embedding service with model loading and error handling.

        Raises:
            RuntimeError: If model loading fails
        """
        self._model: Optional[SentenceTransformer] = None
        self._backend = "not_loaded"
        self._aspect_cache: Dict[str, np.ndarray] = {}
        self._cache_run_id: Optional[str] = None
        self._cache_lock: Lock = Lock()  # Thread safety for cache operations
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0,
            'last_access_time': None
        }
        self._initialize_model()

    @staticmethod
    def _onnx_available() -> bool:
        try:
            import onnxruntime  # noqa: F401
            return True
        except ImportError:
            return False

    def _select_backend(self) -> str:
        """Select best available backend: gpu > onnx > cpu.

        Skips ONNX if available RAM is below 2GB to avoid OOM during export.
        """
        forced = os.getenv("EMBEDDING_BACKEND", "").strip().lower()
        if forced in ("gpu", "onnx", "cpu"):
            logger.info(f"EMBEDDING_BACKEND override: {forced}")
            return forced

        if torch.cuda.is_available():
            return "gpu"

        avail_gb = psutil.virtual_memory().available / (1024 ** 3)
        if avail_gb < 2.0:
            logger.info(
                f"Skipping ONNX for embeddings — only {avail_gb:.1f}GB RAM available. "
                f"Falling back to PyTorch CPU."
            )
            return "cpu"

        if self._onnx_available():
            return "onnx"
        return "cpu"

    def _initialize_model(self) -> None:
        """
        Load the sentence transformer model with backend auto-detection.

        Priority: GPU > ONNX > PyTorch CPU.
        sentence-transformers supports ONNX natively via backend parameter.
        """
        try:
            backend = self._select_backend()
            logger.info(f"Loading embedding model: {self.MODEL_NAME} (backend: {backend})")

            device = "cuda" if backend == "gpu" else "cpu"

            if backend == "onnx":
                self._backend = "onnx-cpu"
                self._model = SentenceTransformer(
                    self.MODEL_NAME,
                    device=device,
                    backend="onnx",
                )
            else:
                self._backend = f"pytorch-{device}"
                self._model = SentenceTransformer(self.MODEL_NAME, device=device)

            # Verify model loaded correctly
            if self._model is None:
                raise RuntimeError("Model loaded but returned None")

            # Test model with a simple embedding
            test_embedding = self._model.encode("test", convert_to_numpy=True)
            if test_embedding.shape[0] != self.EMBEDDING_DIMENSION:
                raise RuntimeError(
                    f"Model output dimension {test_embedding.shape[0]} "
                    f"does not match expected {self.EMBEDDING_DIMENSION}"
                )

            logger.info(
                f"Successfully loaded {self.MODEL_NAME} "
                f"(backend: {self._backend}, dimension: {self.EMBEDDING_DIMENSION})"
            )

        except Exception as e:
            error_msg = f"Failed to load embedding model {self.MODEL_NAME}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def get_single_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Input text to embed
            
        Returns:
            numpy array of shape (384,) containing the embedding
            
        Raises:
            ValueError: If text is empty or None
            RuntimeError: If model is not initialized or embedding fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty or None")
        
        if self._model is None:
            raise RuntimeError("Embedding model is not initialized")
        
        try:
            # Generate embedding
            embedding = self._model.encode(
                text.strip(),
                convert_to_numpy=True,
                normalize_embeddings=True  # Normalize for cosine similarity
            )
            
            # Validate output shape
            if embedding.shape != (self.EMBEDDING_DIMENSION,):
                raise RuntimeError(
                    f"Unexpected embedding shape: {embedding.shape}, "
                    f"expected ({self.EMBEDDING_DIMENSION},)"
                )
            
            return embedding
            
        except Exception as e:
            error_msg = f"Failed to generate embedding for text: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a batch of texts efficiently with memory optimization.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            numpy array of shape (len(texts), 384) containing embeddings
            
        Raises:
            ValueError: If texts list is empty or contains invalid entries
            RuntimeError: If model is not initialized or batch embedding fails
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        if self._model is None:
            raise RuntimeError("Embedding model is not initialized")
        
        # Filter and validate texts
        valid_texts = []
        for i, text in enumerate(texts):
            if not text or not text.strip():
                logger.warning(f"Skipping empty text at index {i}")
                valid_texts.append("")  # Keep placeholder for consistent indexing
            else:
                valid_texts.append(text.strip())
        
        if not any(valid_texts):
            raise ValueError("No valid texts found in input list")
        
        try:
            logger.debug(f"Generating embeddings for {len(valid_texts)} texts")
            
            # Determine optimal batch size based on memory and text count
            optimal_batch_size = self._calculate_optimal_batch_size(len(valid_texts))
            
            # Generate batch embeddings with memory optimization
            embeddings = self._model.encode(
                valid_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,  # Normalize for cosine similarity
                batch_size=optimal_batch_size,
                show_progress_bar=len(valid_texts) > 100,  # Show progress for large batches
                device=self._model.device  # Ensure consistent device usage
            )
            
            # Validate output shape
            expected_shape = (len(valid_texts), self.EMBEDDING_DIMENSION)
            if embeddings.shape != expected_shape:
                raise RuntimeError(
                    f"Unexpected embeddings shape: {embeddings.shape}, "
                    f"expected {expected_shape}"
                )
            
            logger.debug(f"Successfully generated {embeddings.shape[0]} embeddings with batch size {optimal_batch_size}")
            return embeddings
            
        except Exception as e:
            error_msg = f"Failed to generate batch embeddings: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def _calculate_optimal_batch_size(self, num_texts: int) -> int:
        """
        Calculate optimal batch size based on available memory and number of texts.
        
        Args:
            num_texts: Number of texts to process
            
        Returns:
            Optimal batch size for processing
        """
        try:
            # Get available memory
            memory = psutil.virtual_memory()
            available_memory_mb = memory.available / (1024 * 1024)
            
            # Start with default batch size
            batch_size = self.DEFAULT_BATCH_SIZE
            
            # Adjust based on available memory
            if available_memory_mb < self.MEMORY_THRESHOLD_MB:
                # Low memory - reduce batch size
                batch_size = max(self.MIN_BATCH_SIZE, batch_size // 2)
                logger.debug(f"Reduced batch size to {batch_size} due to low memory ({available_memory_mb:.1f}MB available)")
            elif available_memory_mb > self.MEMORY_THRESHOLD_MB * 2:
                # High memory - increase batch size
                batch_size = min(self.MAX_BATCH_SIZE, batch_size * 2)
                logger.debug(f"Increased batch size to {batch_size} due to high memory ({available_memory_mb:.1f}MB available)")
            
            # Adjust based on number of texts
            if num_texts < batch_size:
                batch_size = max(self.MIN_BATCH_SIZE, num_texts)
            
            # Environment variable override
            env_batch_size = os.getenv('EMBEDDING_BATCH_SIZE')
            if env_batch_size:
                try:
                    batch_size = max(self.MIN_BATCH_SIZE, min(self.MAX_BATCH_SIZE, int(env_batch_size)))
                    logger.debug(f"Using environment-specified batch size: {batch_size}")
                except ValueError:
                    logger.warning(f"Invalid EMBEDDING_BATCH_SIZE environment variable: {env_batch_size}")
            
            return batch_size
            
        except Exception as e:
            logger.warning(f"Failed to calculate optimal batch size: {e}, using default: {self.DEFAULT_BATCH_SIZE}")
            return self.DEFAULT_BATCH_SIZE
    
    def get_embeddings_chunked(self, texts: List[str], chunk_size: Optional[int] = None) -> np.ndarray:
        """
        Generate embeddings for large batches using chunked processing for memory efficiency.
        
        This method is useful for processing very large text collections that might
        exceed memory limits with standard batch processing.
        
        Args:
            texts: List of input texts to embed
            chunk_size: Optional chunk size for processing (auto-calculated if None)
            
        Returns:
            numpy array of shape (len(texts), 384) containing embeddings
            
        Raises:
            ValueError: If texts list is empty
            RuntimeError: If model is not initialized or processing fails
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        if self._model is None:
            raise RuntimeError("Embedding model is not initialized")
        
        # Calculate chunk size if not provided
        if chunk_size is None:
            chunk_size = self._calculate_optimal_batch_size(len(texts)) * 4  # Larger chunks for efficiency
        
        logger.info(f"Processing {len(texts)} texts in chunks of {chunk_size}")
        
        all_embeddings = []
        
        try:
            # Process texts in chunks
            for i in range(0, len(texts), chunk_size):
                chunk = texts[i:i + chunk_size]
                logger.debug(f"Processing chunk {i//chunk_size + 1}/{(len(texts) + chunk_size - 1)//chunk_size}")
                
                # Generate embeddings for this chunk
                chunk_embeddings = self.get_embeddings(chunk)
                all_embeddings.append(chunk_embeddings)
            
            # Concatenate all embeddings
            final_embeddings = np.vstack(all_embeddings)
            
            logger.info(f"Successfully processed {len(texts)} texts in {len(all_embeddings)} chunks")
            return final_embeddings
            
        except Exception as e:
            error_msg = f"Failed to generate chunked embeddings: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def cache_aspect_embeddings(self, aspects: List[str], run_id: str = None) -> Dict[str, np.ndarray]:
        """
        Generate and cache aspect embeddings for a processing run.
        
        This method caches aspect embeddings to avoid recomputation during
        a single processing run, but clears the cache between different runs.
        Thread-safe implementation ensures consistent behavior in concurrent environments.
        
        Args:
            aspects: List of aspect texts to embed and cache
            run_id: Optional run identifier for cache invalidation
            
        Returns:
            Dictionary mapping aspect text to embedding array
            
        Raises:
            ValueError: If aspects list is empty
            RuntimeError: If embedding generation fails
        """
        if not aspects:
            raise ValueError("Aspects list cannot be empty")
        
        with self._cache_lock:  # Thread-safe cache operations
            # Clear cache if this is a new run
            if run_id and run_id != self._cache_run_id:
                logger.debug(f"Clearing aspect cache for new run: {run_id}")
                self._aspect_cache.clear()
                self._cache_run_id = run_id
                self._cache_stats['invalidations'] += 1
            
            # Check which aspects need embedding
            aspects_to_embed = []
            cached_aspects = {}
            
            for aspect in aspects:
                if aspect in self._aspect_cache:
                    cached_aspects[aspect] = self._aspect_cache[aspect]
                    self._cache_stats['hits'] += 1
                    logger.debug(f"Using cached embedding for aspect: {aspect}")
                else:
                    aspects_to_embed.append(aspect)
                    self._cache_stats['misses'] += 1
            
            # Update last access time
            self._cache_stats['last_access_time'] = time.time()
            
            # Generate embeddings for uncached aspects (outside the lock for performance)
            if aspects_to_embed:
                logger.info(f"Generating embeddings for {len(aspects_to_embed)} new aspects")
                try:
                    # Release lock during embedding generation to avoid blocking other operations
                    pass  # We'll generate embeddings after the with block
                except Exception as e:
                    error_msg = f"Failed to cache aspect embeddings: {str(e)}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg) from e
        
        # Generate embeddings outside the lock to avoid blocking
        if aspects_to_embed:
            try:
                new_embeddings = self.get_embeddings(aspects_to_embed)
                
                # Re-acquire lock to update cache
                with self._cache_lock:
                    for i, aspect in enumerate(aspects_to_embed):
                        self._aspect_cache[aspect] = new_embeddings[i]
                        cached_aspects[aspect] = new_embeddings[i]
                
                logger.info(f"Cached embeddings for {len(aspects_to_embed)} aspects")
                
            except Exception as e:
                error_msg = f"Failed to cache aspect embeddings: {str(e)}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
        
        return cached_aspects
    
    def clear_aspect_cache(self) -> None:
        """
        Clear the aspect embedding cache.
        
        This method should be called between processing runs to ensure
        fresh caching behavior. Thread-safe implementation.
        """
        with self._cache_lock:
            logger.debug("Clearing aspect embedding cache")
            self._aspect_cache.clear()
            self._cache_run_id = None
            self._cache_stats['invalidations'] += 1
    
    def get_cache_info(self) -> Dict[str, Union[int, str, None, float]]:
        """
        Get information about the current cache state.
        
        Returns:
            Dictionary containing cache statistics and metadata
        """
        with self._cache_lock:
            cache_size_bytes = sum(
                embedding.nbytes for embedding in self._aspect_cache.values()
            ) if self._aspect_cache else 0
            
            return {
                "cached_aspects_count": len(self._aspect_cache),
                "current_run_id": self._cache_run_id,
                "model_name": self.MODEL_NAME,
                "embedding_dimension": self.EMBEDDING_DIMENSION,
                "device": str(self._model.device) if self._model else None,
                "cache_size_bytes": cache_size_bytes,
                "cache_size_mb": round(cache_size_bytes / (1024 * 1024), 2),
                "cache_hits": self._cache_stats['hits'],
                "cache_misses": self._cache_stats['misses'],
                "cache_invalidations": self._cache_stats['invalidations'],
                "cache_hit_rate": (
                    self._cache_stats['hits'] / (self._cache_stats['hits'] + self._cache_stats['misses'])
                    if (self._cache_stats['hits'] + self._cache_stats['misses']) > 0 else 0.0
                ),
                "last_access_time": self._cache_stats['last_access_time']
            }
    
    def reset_cache_stats(self) -> None:
        """
        Reset cache statistics to initial state.
        
        This method is primarily for testing purposes to ensure
        clean state between test runs.
        """
        with self._cache_lock:
            self._cache_stats = {
                'hits': 0,
                'misses': 0,
                'invalidations': 0,
                'last_access_time': None
            }
    
    def get_cache_stats(self) -> Dict[str, Union[int, float, None]]:
        """
        Get detailed cache performance statistics.
        
        Returns:
            Dictionary containing cache performance metrics
        """
        with self._cache_lock:
            total_requests = self._cache_stats['hits'] + self._cache_stats['misses']
            return {
                "cache_hits": self._cache_stats['hits'],
                "cache_misses": self._cache_stats['misses'],
                "total_requests": total_requests,
                "hit_rate": (
                    self._cache_stats['hits'] / total_requests
                    if total_requests > 0 else 0.0
                ),
                "miss_rate": (
                    self._cache_stats['misses'] / total_requests
                    if total_requests > 0 else 0.0
                ),
                "invalidations": self._cache_stats['invalidations'],
                "last_access_time": self._cache_stats['last_access_time']
            }
    
    @property
    def is_initialized(self) -> bool:
        """
        Check if the embedding model is properly initialized.
        
        Returns:
            True if model is loaded and ready, False otherwise
        """
        return self._model is not None
    
    @property
    def model_info(self) -> Dict[str, Union[str, int]]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary containing model metadata
        """
        return {
            "model_name": self.MODEL_NAME,
            "embedding_dimension": self.EMBEDDING_DIMENSION,
            "device": str(self._model.device) if self._model else "not_loaded",
            "is_initialized": self.is_initialized
        }