import os
import ssl
import logging
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apis.settings')

app = Celery('saramsa')

# Get URLs from environment BEFORE Django settings
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Set SSL transport options IMMEDIATELY for rediss:// URLs
# This must happen before config_from_object to prevent backend initialization
if broker_url.startswith('rediss://'):
    app.conf.broker_transport_options = {'ssl_cert_reqs': ssl.CERT_REQUIRED}
    
if result_backend.startswith('rediss://'):
    app.conf.result_backend_transport_options = {'ssl_cert_reqs': ssl.CERT_REQUIRED}

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Force re-set SSL options after config loading to ensure they persist
if broker_url.startswith('rediss://'):
    app.conf.broker_transport_options = {'ssl_cert_reqs': ssl.CERT_REQUIRED}
    
if result_backend.startswith('rediss://'):
    app.conf.result_backend_transport_options = {'ssl_cert_reqs': ssl.CERT_REQUIRED}

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

logger = logging.getLogger(__name__)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.debug(f'Request: {self.request!r}')