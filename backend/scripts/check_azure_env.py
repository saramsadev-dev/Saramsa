#!/usr/bin/env python
"""
Check why Azure OpenAI is not connected: list missing or empty env vars.
Run from backend directory: python scripts/check_azure_env.py
Or from project root: python backend/scripts/check_azure_env.py
"""
import os
import sys
from pathlib import Path

# Ensure backend is on path and load .env from backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

REQUIRED = {
    "AZURE_ENDPOINT_URL": "Azure OpenAI endpoint (e.g. https://YOUR-RESOURCE.openai.azure.com/)",
    "AZURE_DEPLOYMENT_NAME": "Deployment name in Azure Portal (e.g. gpt-4o or gpt-35-turbo)",
    "AZURE_API_KEY": "API key from Azure OpenAI resource",
    "AZURE_API_VERSION": "API version (e.g. 2024-02-15-preview)",
}

def main():
    env_file = BACKEND_DIR / ".env"
    print(f"Backend dir: {BACKEND_DIR}")
    print(f".env file exists: {env_file.exists()}")
    print()
    missing = []
    for key, desc in REQUIRED.items():
        val = os.getenv(key)
        if not val or not str(val).strip():
            missing.append(key)
            print(f"  [MISSING] {key}")
            print(f"            -> {desc}")
        else:
            # Show only that it's set (don't print the key value)
            print(f"  [OK]      {key}")
    print()
    if missing:
        print("Azure is not connected because these env vars are missing or empty.")
        print("Add them to backend/.env (create the file if it doesn't exist):")
        print()
        for k in missing:
            print(f"  {k}=<your-value>")
        print()
        return 1
    print("All Azure OpenAI env vars are set. If you still get 503, check:")
    print("  - AZURE_API_KEY is correct and not expired")
    print("  - AZURE_DEPLOYMENT_NAME matches the deployment name in Azure Portal")
    print("  - AZURE_ENDPOINT_URL has no trailing slash and uses https://")
    return 0

if __name__ == "__main__":
    sys.exit(main())
