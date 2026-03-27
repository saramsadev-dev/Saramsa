from .openai_client import get_azure_client, get_azure_deployment_name
from .utilities import fix_json_string, validate_json_structure
from apis.infrastructure.usage_logging import log_token_usage
from apis.core.error_handlers import handle_service_errors
import os
import time
import logging

# LLM Configuration Constants (deployment name = single source in openai_client)
DEFAULT_MODEL = get_azure_deployment_name()
DEFAULT_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '1300'))
DEFAULT_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
DEFAULT_TOP_P = float(os.getenv('OPENAI_TOP_P', '0.95'))

# Initialize logger BEFORE using it
logger = logging.getLogger("apis.app")

def get_azure_client_instance():
    """
    Lazy initialization of Azure OpenAI Client (sync).
    Called only when needed, not at import time.
    """
    try:
        azure_client = get_azure_client().get_client()
        if not azure_client:
            raise RuntimeError("Azure OpenAI client is not initialized")
        return azure_client
    except Exception as e:
        logger.error(f"Failed to get Azure OpenAI client: {e}")
        raise ConnectionError(f"Azure OpenAI service unavailable: {str(e)}")

def get_async_azure_client_instance():
    """
    Lazy initialization of Azure OpenAI Client (async).
    """
    try:
        async_client = get_azure_client().get_async_client()
        if not async_client:
            raise RuntimeError("Azure OpenAI async client is not initialized")
        return async_client
    except ConnectionError:
        raise
    except Exception as e:
        logger.error("Failed to get Azure OpenAI async client: %s", e)
        raise ConnectionError(
            str(e) if "Missing" in str(e) or "Set these env" in str(e) else f"Azure OpenAI service unavailable: {e}"
        )

@handle_service_errors
async def generate_completions(prompt_instruction, max_tokens=None, user_id=None, project_id=None, task_type=None):
    """
    Generate AI completions using Azure OpenAI with proper error handling and token tracking.

    Args:
        prompt_instruction: The prompt to send to the AI model
        max_tokens: Optional max tokens for output (defaults to DEFAULT_MAX_TOKENS, but should be higher for batch processing)
                   For 25 comments, recommend 4000-5000 tokens
        user_id: User who triggered the call (for usage attribution)
        project_id: Project this call belongs to
        task_type: Type of work (e.g. 'analysis', 'narration', 'aspect_suggestion', 'keyword_update')

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
        azure_client = get_async_azure_client_instance()

        # Time the LLM API call
        t0 = time.perf_counter()
        completion = await azure_client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=chat_prompt,
            max_completion_tokens=effective_max_tokens,
            stream=False,
        )
        latency_ms = (time.perf_counter() - t0) * 1_000

        logger.info("Analysis Complete (%.0fms)", latency_ms)
        result = fix_json_string(completion.choices[0].message.content)

        # Log token usage if usage object available
        actual_usage = None
        try:
            usage = getattr(completion, 'usage', None)
            if usage:
                actual_usage = {
                    "input_tokens": getattr(usage, 'prompt_tokens', None) or getattr(usage, 'input_tokens', None),
                    "output_tokens": getattr(usage, 'completion_tokens', None) or getattr(usage, 'output_tokens', None),
                    "total_tokens": getattr(usage, 'total_tokens', None),
                }
                log_token_usage(
                    user_id=user_id,
                    project_id=project_id,
                    task_type=task_type,
                    vendor="azure_openai",
                    model=DEFAULT_MODEL,
                    input_tokens=actual_usage["input_tokens"],
                    output_tokens=actual_usage["output_tokens"],
                    total_tokens=actual_usage["total_tokens"],
                    latency_ms=latency_ms,
                    metadata={"component": "completion_service.generate_completions"},
                )
        except Exception as e:
            logger.warning(f"Failed to log token usage: {e}")

        # Return result and actual usage so callers can record precise tokens
        return result, actual_usage

    except Exception as e:
        err_msg = str(e).strip()
        logger.error("GPT/Azure OpenAI completion failed: %s", err_msg, exc_info=True)
        if "rate limit" in err_msg.lower() or "429" in err_msg:
            raise ConnectionError("Azure OpenAI rate limit exceeded. Please try again later.")
        if "authentication" in err_msg.lower() or "401" in err_msg or "invalid" in err_msg.lower() and "key" in err_msg.lower():
            raise ConnectionError(
                "Azure OpenAI authentication failed. Check AZURE_API_KEY and AZURE_ENDPOINT_URL in .env"
            )
        if "404" in err_msg or "deployment" in err_msg.lower() or "not found" in err_msg.lower():
            raise ConnectionError(
                "Azure OpenAI deployment not found. Check AZURE_DEPLOYMENT_NAME matches your Azure portal deployment name."
            )
        raise ConnectionError(f"Azure OpenAI error: {err_msg}")