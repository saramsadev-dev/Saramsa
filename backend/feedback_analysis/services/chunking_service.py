"""
Feedback Chunking Service

Handles intelligent text chunking for different types of AI analysis.
Uses comment-count-based batching (25-30 comments per batch) for optimal accuracy.

Moved from aiCore/chunker.py to follow proper Django app architecture.
Now properly organized in the services folder.
"""

import tiktoken
from typing import List, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)


class FeedbackChunkingService:
    """Service for chunking feedback data optimally for AI analysis."""
    
    def __init__(self):
        self.default_model = "gpt-4o-mini"
        # Batch size configuration (comment-count-based, not token-based)
        self.optimal_batch_size = 25  # Best accuracy: 20-30 comments per batch
        self.max_batch_size = 30  # Hard maximum
        self.never_exceed_size = 50  # Safety limit
        # Token limits as safety checks (not primary limit)
        self.sentiment_max_tokens = 8000  # Safety limit (should not be hit with 25 comments)
        self.deep_analysis_max_tokens = 10000  # Safety limit
        self.overlap = 100  # Not used for comment-based chunking, kept for backward compatibility
    
    def chunk_feedback_for_sentiment(self, feedback_data: str, model: str = None) -> List[str]:
        """
        Chunk feedback data optimally for sentiment analysis.
        
        Uses comment-count-based batching (25 comments per batch) for optimal accuracy.
        Tries to preserve individual comment boundaries.
        
        Args:
            feedback_data: Raw feedback text
            model: AI model name (defaults to gpt-4o-mini)
            
        Returns:
            List of text chunks optimized for sentiment analysis
        """
        model = model or self.default_model
        
        try:
            # Try to split by comment boundaries first
            comments = self._split_into_comments(feedback_data)
            
            if len(comments) > 1:
                # If we have identifiable comments, chunk by comment count (not tokens)
                return self._chunk_by_comment_count(comments, model, self.optimal_batch_size, self.sentiment_max_tokens)
            else:
                # Fallback to standard chunking (for unstructured text)
                logger.warning("Could not identify comment boundaries, using token-based chunking")
                return self._chunk_text_standard(feedback_data, model, self.sentiment_max_tokens, self.overlap)
                
        except Exception as e:
            logger.warning(f"Error in smart chunking, falling back to standard: {e}")
            return self._chunk_text_standard(feedback_data, model, self.sentiment_max_tokens, self.overlap)
    
    def chunk_feedback_for_deep_analysis(self, feedback_data: str, model: str = None) -> List[str]:
        """
        Chunk feedback data optimally for deep analysis and work item generation.
        
        Uses comment-count-based batching (25 comments per batch) for optimal accuracy.
        
        Args:
            feedback_data: Raw feedback text
            model: AI model name (defaults to gpt-4o-mini)
            
        Returns:
            List of text chunks optimized for deep analysis
        """
        model = model or self.default_model
        
        try:
            # Try to split by comment boundaries first
            comments = self._split_into_comments(feedback_data)
            
            if len(comments) > 1:
                # If we have identifiable comments, chunk by comment count (not tokens)
                return self._chunk_by_comment_count(comments, model, self.optimal_batch_size, self.deep_analysis_max_tokens)
            else:
                # Fallback to standard chunking
                logger.warning("Could not identify comment boundaries, using token-based chunking")
                return self._chunk_text_standard(feedback_data, model, self.deep_analysis_max_tokens, self.overlap * 2)
                
        except Exception as e:
            logger.warning(f"Error in smart chunking, falling back to standard: {e}")
            return self._chunk_text_standard(feedback_data, model, self.deep_analysis_max_tokens, self.overlap * 2)
    
    def _split_into_comments(self, feedback_data: str) -> List[str]:
        """
        Try to intelligently split feedback into individual comments.
        
        Looks for common patterns like:
        - JSON array of comments
        - CSV-like structure
        - Line-separated comments
        - Numbered comments
        """
        # Try JSON array first
        if feedback_data.strip().startswith('[') and feedback_data.strip().endswith(']'):
            try:
                import json
                data = json.loads(feedback_data)
                if isinstance(data, list):
                    return [str(item) for item in data if item]
            except:
                pass
        
        # Try line separation with common delimiters
        lines = feedback_data.split('\n')
        if len(lines) > 1:
            # Filter out only empty lines (not short lines - short comments are valid!)
            comments = [line.strip() for line in lines if line.strip()]
            if len(comments) > 1:
                return comments
        
        # Try numbered comments (1., 2., etc.)
        numbered_pattern = r'^\d+\.\s*(.+)'
        numbered_comments = []
        for line in lines:
            match = re.match(numbered_pattern, line.strip())
            if match:
                numbered_comments.append(match.group(1))
        
        if len(numbered_comments) > 1:
            return numbered_comments
        
        # If no clear structure, return as single item
        return [feedback_data]
    
    def _chunk_by_comment_count(self, comments: List[str], model: str, target_batch_size: int, max_tokens: int) -> List[str]:
        """
        Group comments into batches by comment count (not tokens).
        
        This is the CORRECT approach: batch by comment count (25-30 per batch)
        for optimal LLM accuracy, not by token count.
        
        Args:
            comments: List of individual comments
            model: AI model name for token encoding
            target_batch_size: Target number of comments per batch (25 recommended)
            max_tokens: Maximum tokens as safety limit (should not be hit)
            
        Returns:
            List of text chunks (each chunk contains target_batch_size comments)
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to a common encoding if model not found
            encoding = tiktoken.get_encoding("cl100k_base")
        
        chunks = []
        current_batch = []
        current_tokens = 0
        
        for i, comment in enumerate(comments):
            comment_tokens = len(encoding.encode(comment))
            
            # Safety check: if single comment exceeds token limit, warn but include it
            if comment_tokens > max_tokens:
                logger.warning(f"Comment {i} exceeds token limit ({comment_tokens} > {max_tokens}), including anyway")
            
            # Check if adding this comment would exceed safety token limit
            if current_tokens + comment_tokens > max_tokens and current_batch:
                # Start new batch before adding this comment
                chunks.append('\n'.join(current_batch))
                current_batch = [comment]
                current_tokens = comment_tokens
            # Check if we've reached target batch size
            elif len(current_batch) >= target_batch_size:
                # Start new batch
                chunks.append('\n'.join(current_batch))
                current_batch = [comment]
                current_tokens = comment_tokens
            else:
                # Add comment to current batch
                current_batch.append(comment)
                current_tokens += comment_tokens
        
        # Add the last batch if it has content
        if current_batch:
            chunks.append('\n'.join(current_batch))
        
        logger.info(f"Chunked {len(comments)} comments into {len(chunks)} batches (target: {target_batch_size} comments per batch)")
        
        # Validate batch sizes
        for i, chunk in enumerate(chunks):
            chunk_comments = chunk.split('\n')
            if len(chunk_comments) > self.never_exceed_size:
                logger.error(f"Batch {i} has {len(chunk_comments)} comments, exceeds safety limit of {self.never_exceed_size}")
            elif len(chunk_comments) > self.max_batch_size:
                logger.warning(f"Batch {i} has {len(chunk_comments)} comments, exceeds recommended limit of {self.max_batch_size}")
        
        return chunks
    
    def _chunk_by_comments(self, comments: List[str], model: str, max_tokens: int) -> List[str]:
        """
        OLD METHOD: Group comments into chunks by token limit (DEPRECATED).
        
        This method is kept for backward compatibility but is NOT recommended.
        Use _chunk_by_comment_count instead for optimal accuracy.
        """
        logger.warning("Using deprecated token-based chunking. Use comment-count-based chunking for better accuracy.")
        return self._chunk_by_comment_count(comments, model, self.optimal_batch_size, max_tokens)
    
    def _chunk_text_standard(self, text: str, model: str, max_tokens: int, overlap: int) -> List[str]:
        """
        Standard text chunking with overlap (original chunker logic).
        
        This is the fallback method when smart chunking isn't possible
        (e.g., unstructured text without clear comment boundaries).
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to a common encoding if model not found
            encoding = tiktoken.get_encoding("cl100k_base")
        
        encoded_text = encoding.encode(text)
        
        chunks = []
        start = 0
        while start < len(encoded_text):
            end = start + max_tokens
            chunk = encoded_text[start:end]
            chunks.append(encoding.decode(chunk))
            start = end - overlap  # Move the start forward with overlap
        
        return chunks
    
    def get_chunk_info(self, feedback_data: str, model: str = None) -> Dict[str, Any]:
        """
        Get information about how feedback would be chunked.
        
        Useful for debugging and optimization.
        """
        model = model or self.default_model
        
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        
        comments = self._split_into_comments(feedback_data)
        total_tokens = len(encoding.encode(feedback_data))
        
        sentiment_chunks = self.chunk_feedback_for_sentiment(feedback_data, model)
        deep_analysis_chunks = self.chunk_feedback_for_deep_analysis(feedback_data, model)
        
        # Calculate comments per chunk
        sentiment_chunk_sizes = [len(chunk.split('\n')) for chunk in sentiment_chunks]
        deep_chunk_sizes = [len(chunk.split('\n')) for chunk in deep_analysis_chunks]
        
        return {
            "total_comments": len(comments),
            "total_tokens": total_tokens,
            "total_characters": len(feedback_data),
            "optimal_batch_size": self.optimal_batch_size,
            "sentiment_analysis": {
                "chunk_count": len(sentiment_chunks),
                "comments_per_chunk": sentiment_chunk_sizes,
                "avg_comments_per_chunk": sum(sentiment_chunk_sizes) / len(sentiment_chunk_sizes) if sentiment_chunk_sizes else 0,
                "max_tokens_per_chunk": self.sentiment_max_tokens,
            },
            "deep_analysis": {
                "chunk_count": len(deep_analysis_chunks),
                "comments_per_chunk": deep_chunk_sizes,
                "avg_comments_per_chunk": sum(deep_chunk_sizes) / len(deep_chunk_sizes) if deep_chunk_sizes else 0,
                "max_tokens_per_chunk": self.deep_analysis_max_tokens,
            }
        }


# Global service instance
_chunking_service = None

def get_chunking_service() -> FeedbackChunkingService:
    """Get the global chunking service instance."""
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = FeedbackChunkingService()
    return _chunking_service
