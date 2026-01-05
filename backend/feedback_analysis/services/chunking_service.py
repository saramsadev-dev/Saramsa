"""
Feedback Chunking Service

Handles intelligent text chunking for different types of AI analysis.
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
        self.sentiment_max_tokens = 2500  # Smaller chunks for sentiment analysis
        self.deep_analysis_max_tokens = 4000  # Larger chunks for deep analysis
        self.overlap = 100
    
    def chunk_feedback_for_sentiment(self, feedback_data: str, model: str = None) -> List[str]:
        """
        Chunk feedback data optimally for sentiment analysis.
        
        Uses smaller chunks and tries to preserve individual comment boundaries.
        
        Args:
            feedback_data: Raw feedback text
            model: AI model name (defaults to gpt-4o-mini)
            
        Returns:
            List of text chunks optimized for sentiment analysis
        """
        model = model or self.default_model
        max_tokens = self.sentiment_max_tokens
        
        try:
            # Try to split by comment boundaries first
            comments = self._split_into_comments(feedback_data)
            
            if len(comments) > 1:
                # If we have identifiable comments, chunk by grouping comments
                return self._chunk_by_comments(comments, model, max_tokens)
            else:
                # Fallback to standard chunking
                return self._chunk_text_standard(feedback_data, model, max_tokens, self.overlap)
                
        except Exception as e:
            logger.warning(f"Error in smart chunking, falling back to standard: {e}")
            return self._chunk_text_standard(feedback_data, model, max_tokens, self.overlap)
    
    def chunk_feedback_for_deep_analysis(self, feedback_data: str, model: str = None) -> List[str]:
        """
        Chunk feedback data optimally for deep analysis and work item generation.
        
        Uses larger chunks with more context to better understand relationships
        between different pieces of feedback.
        
        Args:
            feedback_data: Raw feedback text
            model: AI model name (defaults to gpt-4o-mini)
            
        Returns:
            List of text chunks optimized for deep analysis
        """
        model = model or self.default_model
        max_tokens = self.deep_analysis_max_tokens
        
        # For deep analysis, we want larger chunks with more context
        return self._chunk_text_standard(feedback_data, model, max_tokens, self.overlap * 2)
    
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
            # Filter out empty lines and very short lines
            comments = [line.strip() for line in lines if len(line.strip()) > 10]
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
    
    def _chunk_by_comments(self, comments: List[str], model: str, max_tokens: int) -> List[str]:
        """
        Group comments into chunks that fit within token limits.
        
        Tries to keep related comments together while respecting token limits.
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to a common encoding if model not found
            encoding = tiktoken.get_encoding("cl100k_base")
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for comment in comments:
            comment_tokens = len(encoding.encode(comment))
            
            # If adding this comment would exceed limit, start new chunk
            if current_tokens + comment_tokens > max_tokens and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [comment]
                current_tokens = comment_tokens
            else:
                current_chunk.append(comment)
                current_tokens += comment_tokens
        
        # Add the last chunk if it has content
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def _chunk_text_standard(self, text: str, model: str, max_tokens: int, overlap: int) -> List[str]:
        """
        Standard text chunking with overlap (original chunker logic).
        
        This is the fallback method when smart chunking isn't possible.
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
    
    def get_chunk_info(self, text: str, model: str = None) -> Dict[str, Any]:
        """
        Get information about how text would be chunked.
        
        Useful for debugging and optimization.
        """
        model = model or self.default_model
        
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        
        total_tokens = len(encoding.encode(text))
        
        sentiment_chunks = self.chunk_feedback_for_sentiment(text, model)
        deep_analysis_chunks = self.chunk_feedback_for_deep_analysis(text, model)
        
        return {
            "total_tokens": total_tokens,
            "total_characters": len(text),
            "sentiment_analysis": {
                "chunk_count": len(sentiment_chunks),
                "max_tokens_per_chunk": self.sentiment_max_tokens,
                "chunks": [len(encoding.encode(chunk)) for chunk in sentiment_chunks]
            },
            "deep_analysis": {
                "chunk_count": len(deep_analysis_chunks),
                "max_tokens_per_chunk": self.deep_analysis_max_tokens,
                "chunks": [len(encoding.encode(chunk)) for chunk in deep_analysis_chunks]
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