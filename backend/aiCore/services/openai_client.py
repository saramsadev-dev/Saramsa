from openai import AzureOpenAI, AsyncAzureOpenAI
from threading import Lock
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("apis.app")

AZURE_OPENAI = {
    "ENDPOINT_URL": os.getenv('ENDPOINT_URL'),
    "DEPLOYMENT_NAME": os.getenv('DEPLOYMENT_NAME'),
    "API_KEY": os.getenv('API_KEY'),
    "API_VERSION": os.getenv('API_VERSION'),
}

class AzureOpenAIClient:
    """
    Thread-safe singleton for Azure OpenAI client with connection validation.
    """
    _instance = None
    _lock = Lock()  # Thread-safe initialization
    
    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:  # Ensure thread safety
                if not cls._instance:
                    cls._instance = super().__new__(cls, *args, **kwargs)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize the Azure OpenAI client instance with validation.
        """
        # Validate configuration
        missing_configs = []
        for key, value in AZURE_OPENAI.items():
            if not value:
                missing_configs.append(key)

        if missing_configs:
            logger.error(f"Missing Azure OpenAI configuration: {missing_configs}")
            raise ValueError(f"Missing required Azure OpenAI configuration: {', '.join(missing_configs)}")

        try:
            self.client = AzureOpenAI(
                azure_endpoint=AZURE_OPENAI["ENDPOINT_URL"],
                api_key=AZURE_OPENAI["API_KEY"],
                api_version=AZURE_OPENAI["API_VERSION"],
            )
            self.async_client = AsyncAzureOpenAI(
                azure_endpoint=AZURE_OPENAI["ENDPOINT_URL"],
                api_key=AZURE_OPENAI["API_KEY"],
                api_version=AZURE_OPENAI["API_VERSION"],
            )
            logger.info("Azure OpenAI client initialized successfully (sync + async)")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            raise ConnectionError(f"Failed to initialize Azure OpenAI client: {e}")

    def get_client(self):
        """
        Get the initialized sync Azure OpenAI client instance.
        """
        if not hasattr(self, 'client') or self.client is None:
            raise ConnectionError("Azure OpenAI client is not initialized")
        return self.client

    def get_async_client(self):
        """
        Get the initialized async Azure OpenAI client instance.
        """
        if not hasattr(self, 'async_client') or self.async_client is None:
            raise ConnectionError("Azure OpenAI async client is not initialized")
        return self.async_client
    
    def test_connection(self) -> bool:
        """
        Test the connection to Azure OpenAI service.
        
        Returns:
            bool: True if connection is successful
            
        Raises:
            ConnectionError: If connection test fails
        """
        try:
            client = self.get_client()
            # Simple test call to verify connection
            response = client.chat.completions.create(
                model=AZURE_OPENAI["DEPLOYMENT_NAME"] or "gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
                max_completion_tokens=1
            )
            logger.info("Azure OpenAI connection test successful")
            return True
        except Exception as e:
            logger.error(f"Azure OpenAI connection test failed: {e}")
            raise ConnectionError(f"Azure OpenAI connection test failed: {e}")


# Global instance for easy access
_azure_client = None

def get_azure_client() -> AzureOpenAIClient:
    """Get the global Azure OpenAI client instance."""
    global _azure_client
    if _azure_client is None:
        _azure_client = AzureOpenAIClient()
    return _azure_client