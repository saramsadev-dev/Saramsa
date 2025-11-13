from openai import AzureOpenAI
from threading import Lock
#from .settings import AZURE_OPENAI
import os
from dotenv import load_dotenv
load_dotenv()

AZURE_OPENAI = {
    "ENDPOINT_URL": os.getenv('ENDPOINT_URL'),
    "DEPLOYMENT_NAME": os.getenv('DEPLOYMENT_NAME'),
    "API_KEY": os.getenv('API_KEY'),
    "API_VERSION": os.getenv('API_VERSION'),
}
class AzureOpenAIClient:
    """
    Singleton for Azure OpenAI client.
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
        Initialize the Azure OpenAI client instance.
        """
        self.client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI["ENDPOINT_URL"],
            api_key=AZURE_OPENAI["API_KEY"],
            api_version=AZURE_OPENAI["API_VERSION"],
        )

    def get_client(self):
        """
        Get the initialized Azure OpenAI client instance.
        """
        return self.client
