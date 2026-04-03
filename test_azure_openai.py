"""Test Azure OpenAI API connection."""
import os
import sys
import django

# Setup Django to get Azure config
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apis.settings')
django.setup()

from aiCore.services.openai_client import AzureOpenAIClient, get_azure_deployment_name, AZURE_OPENAI

print("=== Azure OpenAI Configuration ===")
print(f"Endpoint URL: {AZURE_OPENAI.get('ENDPOINT_URL', 'NOT SET')[:50]}...")
print(f"Deployment Name: {AZURE_OPENAI.get('DEPLOYMENT_NAME', 'NOT SET')}")
print(f"API Version: {AZURE_OPENAI.get('API_VERSION', 'NOT SET')}")
print(f"API Key: {'SET' if AZURE_OPENAI.get('API_KEY') else 'NOT SET'}")

print("\n=== Testing Connection ===")
try:
    client_wrapper = AzureOpenAIClient()
    client = client_wrapper.get_client()
    print("[OK] Azure OpenAI client initialized successfully")

    # Test a simple completion
    print("\n=== Testing Simple Completion ===")
    deployment = get_azure_deployment_name()
    print(f"Using deployment: {deployment}")

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, API is working!' and nothing else."}
        ],
        max_completion_tokens=200  # GPT-5-mini uses reasoning tokens, need more headroom
    )

    result = response.choices[0].message.content
    print(f"[OK] Response received: '{result}'")
    print(f"[OK] Response length: {len(result) if result else 0} chars")
    print(f"[OK] Tokens used: {response.usage.total_tokens}")

    if not result or len(result.strip()) == 0:
        print("[WARNING] Response is empty or whitespace-only!")
        print(f"[DEBUG] Full response: {response}")
        print(f"[DEBUG] Finish reason: {response.choices[0].finish_reason}")

    # Test with JSON response
    print("\n=== Testing JSON Response ===")
    response2 = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You respond only with valid JSON."},
            {"role": "user", "content": 'Return this JSON: {"status": "ok", "message": "API working"}'}
        ],
        max_completion_tokens=300  # GPT-5-mini uses reasoning tokens
    )

    result2 = response2.choices[0].message.content
    print(f"[OK] JSON response: {result2}")

    print("\n=== All Tests Passed ===")
    print("Azure OpenAI API is working correctly!")

except ValueError as e:
    print(f"[ERROR] Configuration error: {e}")
    print("\nPlease check backend/.env file has:")
    print("  AZURE_ENDPOINT_URL=https://your-resource.openai.azure.com/")
    print("  AZURE_DEPLOYMENT_NAME=your-deployment-name")
    print("  AZURE_API_KEY=your-api-key")
    print("  AZURE_API_VERSION=2024-02-15-preview")

except ConnectionError as e:
    print(f"[ERROR] Connection error: {e}")

except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()
