import os
import ssl
import sys
import logging
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apis.settings')

app = Celery('saramsa')

# Windows compatibility: Use 'solo' pool on Windows (single process, no forking)
# On Unix/Linux, use default 'prefork' pool for better performance
logger = logging.getLogger(__name__)
if sys.platform == 'win32':
    app.conf.worker_pool = 'solo'
    logger.info("Running on Windows - using 'solo' worker pool")

# Get URLs from environment BEFORE Django settings (Azure Redis)
broker_url = os.getenv('CELERY_BROKER_URL')
result_backend = os.getenv('CELERY_RESULT_BACKEND')

# Add SSL certificate requirements to Redis URLs for Azure Redis
if broker_url and broker_url.startswith('rediss://'):
    # Append ssl_cert_reqs parameter to URL if not already present
    if 'ssl_cert_reqs' not in broker_url:
        separator = '&' if '?' in broker_url else '?'
        # Use CERT_NONE as the value (required by Celery Redis backend)
        broker_url = f"{broker_url}{separator}ssl_cert_reqs=CERT_NONE"
        # Update environment variable for settings.py
        os.environ['CELERY_BROKER_URL'] = broker_url
    app.conf.broker_url = broker_url
    app.conf.broker_transport_options = {'ssl_cert_reqs': ssl.CERT_NONE}
    
if result_backend and result_backend.startswith('rediss://'):
    # Append ssl_cert_reqs parameter to URL if not already present
    if 'ssl_cert_reqs' not in result_backend:
        separator = '&' if '?' in result_backend else '?'
        # Use CERT_NONE as the value (required by Celery Redis backend)
        result_backend = f"{result_backend}{separator}ssl_cert_reqs=CERT_NONE"
        # Update environment variable for settings.py
        os.environ['CELERY_RESULT_BACKEND'] = result_backend
    app.conf.result_backend = result_backend
    app.conf.result_backend_transport_options = {'ssl_cert_reqs': ssl.CERT_NONE}

app.config_from_object('django.conf:settings', namespace='CELERY')

# Re-apply Windows pool setting after config loading (in case settings.py overrides it)
if sys.platform == 'win32':
    app.conf.worker_pool = 'solo'

# Force re-set URLs and SSL options after config loading to ensure they persist
if broker_url and broker_url.startswith('rediss://'):
    # Re-read from environment in case settings.py modified it
    updated_broker_url = os.getenv('CELERY_BROKER_URL', broker_url)
    if 'ssl_cert_reqs' not in updated_broker_url:
        separator = '&' if '?' in updated_broker_url else '?'
        updated_broker_url = f"{updated_broker_url}{separator}ssl_cert_reqs=CERT_NONE"
    app.conf.broker_url = updated_broker_url
    app.conf.broker_transport_options = {'ssl_cert_reqs': ssl.CERT_NONE}
    
if result_backend and result_backend.startswith('rediss://'):
    # Re-read from environment in case settings.py modified it
    updated_result_backend = os.getenv('CELERY_RESULT_BACKEND', result_backend)
    if 'ssl_cert_reqs' not in updated_result_backend:
        separator = '&' if '?' in updated_result_backend else '?'
        updated_result_backend = f"{updated_result_backend}{separator}ssl_cert_reqs=CERT_NONE"
    app.conf.result_backend = updated_result_backend
    app.conf.result_backend_transport_options = {'ssl_cert_reqs': ssl.CERT_NONE}

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.debug(f'Request: {self.request!r}')