from django.apps import AppConfig


class AiCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aiCore'
    verbose_name = 'AI Core Services'
    
    def ready(self):
        """Initialize AI services when Django starts."""
        try:
            # Test Azure OpenAI connection on startup
            from .services.openai_client import get_azure_client
            client = get_azure_client()

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"AI Core initialization warning: {e}")
            # Don't raise exception to allow Django to start even if AI is not configured