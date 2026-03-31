from django.apps import AppConfig


class AiCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aiCore'
    verbose_name = 'AI Core Services'
    
    def ready(self):
        """AI Core app startup — client is initialized lazily on first use."""
        pass  # Azure OpenAI client is created on first call to get_azure_client()