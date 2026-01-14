from .openai_client import get_azure_client
from .utilities import fix_json_string, validate_json_structure
from apis.infrastructure.usage_logging import log_token_usage
from apis.core.error_handlers import handle_service_errors
import os
import logging

# LLM Configuration Constants
DEFAULT_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
DEFAULT_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '1300'))
DEFAULT_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
DEFAULT_TOP_P = float(os.getenv('OPENAI_TOP_P', '0.95'))

# Get the singleton client
azure_client = get_azure_client().get_client()

logger = logging.getLogger("apis.app")

@handle_service_errors
async def generate_completions(prompt_instruction, max_tokens=None):
    """
    Generate AI completions using Azure OpenAI with proper error handling and token tracking.
    
    Args:
        prompt_instruction: The prompt to send to the AI model
        max_tokens: Optional max tokens for output (defaults to DEFAULT_MAX_TOKENS, but should be higher for batch processing)
                   For 25 comments, recommend 4000-5000 tokens
        
    Returns:
        Processed completion result
        
    Raises:
        ValueError: If prompt is invalid
        ConnectionError: If AI service is unavailable
    """
    if not prompt_instruction or not prompt_instruction.strip():
        raise ValueError("Prompt instruction cannot be empty")
    
    # Use provided max_tokens or default, but ensure minimum for batch processing
    effective_max_tokens = max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS
    # If using default and it's too low, increase it (better to err on the side of more tokens)
    if effective_max_tokens < 3000:
        effective_max_tokens = max(effective_max_tokens, 4000)  # Minimum 4000 for batch processing
        logger.info(f"Adjusted max_tokens to {effective_max_tokens} for batch processing (was {max_tokens or DEFAULT_MAX_TOKENS})")
    
    chat_prompt = [
        {
            "role": "system",
            "content": prompt_instruction
        }
    ]
    logger.info("Analysing Sentiments...")
    
    try:
        # Generate the completion using the singleton client
        completion = azure_client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=chat_prompt,
            max_tokens=effective_max_tokens,
            temperature=DEFAULT_TEMPERATURE,
            top_p=DEFAULT_TOP_P,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=False,
        )
        
        logger.info("Analysis Complete")
        result = fix_json_string(completion.choices[0].message.content)
        
        # Log token usage if usage object available
        try:
            usage = getattr(completion, 'usage', None)
            if usage:
                log_token_usage(
                    vendor="azure_openai",
                    model=DEFAULT_MODEL,
                    input_tokens=getattr(usage, 'prompt_tokens', None) or getattr(usage, 'input_tokens', None),
                    output_tokens=getattr(usage, 'completion_tokens', None) or getattr(usage, 'output_tokens', None),
                    total_tokens=getattr(usage, 'total_tokens', None),
                    cost_usd=None,
                    metadata={"component": "completion_service.generate_completions"},
                )
        except Exception as e:
            logger.warning(f"Failed to log token usage: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating completion: {e}")
        if "rate limit" in str(e).lower():
            raise ConnectionError("AI service rate limit exceeded. Please try again later.")
        elif "authentication" in str(e).lower():
            raise ConnectionError("AI service authentication failed. Please check configuration.")
        else:
            raise ConnectionError(f"AI service unavailable: {str(e)}")