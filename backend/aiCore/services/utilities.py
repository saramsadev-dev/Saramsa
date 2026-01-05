import re
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("apis.app")

def flatten_feedback(data: List[Dict[str, Any]]) -> List[str]:
    """
    Extract feedback text from data structures.
    
    Args:
        data: List of feedback entries with "Feedback" key
        
    Returns:
        List of feedback text strings
    """
    if not data or not isinstance(data, list):
        return []
    
    feedback_texts = []
    for entry in data:
        if isinstance(entry, dict) and "Feedback" in entry:
            feedback_texts.append(str(entry["Feedback"]))
        elif isinstance(entry, str):
            feedback_texts.append(entry)
    
    return feedback_texts

def fix_json_string(faulty_json: str) -> str:
    """
    Clean and fix malformed JSON strings from LLM responses.
    
    Args:
        faulty_json: Potentially malformed JSON string
        
    Returns:
        Cleaned JSON string
        
    Raises:
        ValueError: If input is empty or None
    """
    if not faulty_json:
        raise ValueError("Input JSON string cannot be empty")
    
    try:
        # Step 1: Replace escaped newlines and quotes
        cleaned_json = faulty_json.replace(r'\\n', '\n')  # Unescape newlines
        cleaned_json = cleaned_json.replace(r'\\"', '"')   # Unescape quotes
        cleaned_json = cleaned_json.replace(r'json', '')   # Remove stray 'json' text
        
        # Step 2: Clean additional escape characters
        cleaned_json = re.sub(r'\\\\"', '"', cleaned_json)
        
        # Step 3: Remove unwanted stray characters (non-alphanumeric, non-structural)
        cleaned_json = re.sub(r'[^a-zA-Z0-9\s\[\]\{\}\:,\.\-\"\\n]', '', cleaned_json)
        
        # Step 4: Normalize whitespace - convert newlines/carriage returns to spaces
        cleaned_json = re.sub(r'[\n\r]+', ' ', cleaned_json)
        cleaned_json = cleaned_json.strip()
        
        # Step 5: Ensure the string has opening and closing braces for valid JSON structure
        if not cleaned_json.startswith("{"):
            cleaned_json = "{" + cleaned_json
        if not cleaned_json.endswith("}"):
            cleaned_json = cleaned_json + "}"
        
        # Step 6: Validate the JSON is parseable
        try:
            json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON validation failed after cleaning: {e}")
            # Return a minimal valid JSON structure
            return '{"error": "Failed to parse LLM response", "raw_content": "' + faulty_json[:100] + '"}'
        
        return cleaned_json
        
    except Exception as e:
        logger.error(f"Error fixing JSON string: {e}")
        return '{"error": "JSON processing failed", "raw_content": "' + str(faulty_json)[:100] + '"}'

def validate_json_structure(cleaned_json: str, validation_type: int = 0) -> Optional[Dict[str, Any]]:
    """
    Validate the structure of the JSON after parsing.
    
    Args:
        cleaned_json: JSON string to validate
        validation_type: 0 for sentiment analysis, 1 for deep analysis
        
    Returns:
        Parsed JSON if valid, None if invalid
    """
    try:
        parsed_json = json.loads(cleaned_json)
        
        # Define the expected schema structures
        sentiment_required_fields = [
            "sentiment_summary", "feature_asba", "emoji_analysis", 
            "positive_keywords", "negative_keywords"
        ]
        deep_analysis_required_fields = [
            "negative_summary", "action_items"
        ]
        
        required_fields = sentiment_required_fields if validation_type == 0 else deep_analysis_required_fields
        
        # Validate root-level fields
        missing_fields = [field for field in required_fields if field not in parsed_json]
        if missing_fields:
            logger.warning(f"Missing required root-level fields: {missing_fields}")
            return None

        # Validate sentiment_summary structure (for sentiment analysis)
        if validation_type == 0 and "sentiment_summary" in parsed_json:
            sentiment_summary = parsed_json["sentiment_summary"]
            required_sentiment_keys = ["positive", "negative", "neutral"]
            if not all(isinstance(sentiment_summary.get(k), str) for k in required_sentiment_keys):
                logger.warning("Invalid sentiment_summary structure")
                return None

            # Validate feature_asba structure
            if "feature_asba" in parsed_json:
                for i, feature in enumerate(parsed_json["feature_asba"]):
                    if not isinstance(feature, dict):
                        continue
                    required_feature_keys = ["feature", "sentiment", "keywords", "explanations"]
                    if not all(k in feature for k in required_feature_keys):
                        logger.warning(f"Missing keys in feature entry {i}: {feature.get('feature', 'unknown')}")
                        continue
                    
                    feature_sentiment = feature.get("sentiment", {})
                    if not all(isinstance(feature_sentiment.get(k), str) for k in required_sentiment_keys):
                        logger.warning(f"Invalid sentiment structure for feature: {feature.get('feature')}")
                        continue

            # Validate emoji_analysis
            if "emoji_analysis" in parsed_json:
                emoji_analysis = parsed_json["emoji_analysis"]
                if not (isinstance(emoji_analysis.get("top_emojis"), list) and 
                        isinstance(emoji_analysis.get("overall_sentiment"), str)):
                    logger.warning("Invalid emoji_analysis structure")
                    return None

        # Validate action_items (for both types)
        if "action_items" in parsed_json:
            action_items = parsed_json["action_items"]
            required_action_categories = ["feature_requests", "bugs", "change_requests"]
            if not all(k in action_items and isinstance(action_items[k], list) 
                      for k in required_action_categories):
                logger.warning("Invalid action_items structure")
                return None

        # If all checks pass
        logger.info("JSON structure validation passed")
        return parsed_json

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return None
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return None

def sanitize_llm_output(output: str, max_length: int = 10000) -> str:
    """
    Sanitize LLM output for security and length.
    
    Args:
        output: Raw LLM output
        max_length: Maximum allowed length
        
    Returns:
        Sanitized output string
    """
    if not output:
        return ""
    
    # Truncate if too long
    if len(output) > max_length:
        output = output[:max_length] + "... [truncated]"
        logger.warning(f"LLM output truncated to {max_length} characters")
    
    # Remove potentially dangerous content
    # Remove script tags and other potentially harmful content
    output = re.sub(r'<script[^>]*>.*?</script>', '', output, flags=re.IGNORECASE | re.DOTALL)
    output = re.sub(r'<iframe[^>]*>.*?</iframe>', '', output, flags=re.IGNORECASE | re.DOTALL)
    
    return output.strip()

def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON content from mixed text that might contain JSON.
    
    Args:
        text: Text that might contain JSON
        
    Returns:
        Extracted JSON string or None if not found
    """
    if not text:
        return None
    
    # Try to find JSON-like content between braces
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    for match in matches:
        try:
            # Test if it's valid JSON
            json.loads(match)
            return match
        except json.JSONDecodeError:
            continue
    
    return None