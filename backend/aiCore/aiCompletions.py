from .aiClient import AzureOpenAIClient
from .utilities import fix_json_string, validate_json_structure
from apis.usage_logging import log_token_usage

# Get the singleton client
azure_client = AzureOpenAIClient().get_client()

async def generate_completions(prompt_instruction):
    chat_prompt = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": prompt_instruction,
                }
            ],
        }
    ]
    chat_prompt = [
        {
            "role": "system",
            "content": prompt_instruction
        }
    ]
    print ("Analysing Sentiments...")
    # Generate the completion using the singleton client
    completion = azure_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=chat_prompt,
        max_tokens=1300,
        temperature=0.7,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=False,
    )
    
    print ("Analysis Complete")
    result = fix_json_string(completion.choices[0].message.content)
    # Log token usage if usage object available
    try:
        usage = getattr(completion, 'usage', None)
        if usage:
            log_token_usage(
                vendor="azure_openai",
                model="gpt-4o-mini",
                input_tokens=getattr(usage, 'prompt_tokens', None) or getattr(usage, 'input_tokens', None),
                output_tokens=getattr(usage, 'completion_tokens', None) or getattr(usage, 'output_tokens', None),
                total_tokens=getattr(usage, 'total_tokens', None),
                cost_usd=None,
                metadata={"component": "aiCompletions.generate_completions"},
            )
    except Exception:
        pass
    return result
    