from pathlib import Path
import os
import ssl
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
os.makedirs(BASE_DIR / 'logs', exist_ok=True)


SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-your-secret-key-here-change-in-production')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Backend's own URL in production (e.g. https://saramsa-backend-xxx.centralus-01.azurewebsites.net).
# When set, this host is added to ALLOWED_HOSTS so Azure can route to the app.
BACKEND_BASE_URL = os.getenv('BACKEND_BASE_URL', '').rstrip('/')
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', '').rstrip('/')

_allowed = os.getenv("ALLOWED_HOSTS", "*").split(",")
if BACKEND_BASE_URL:
    from urllib.parse import urlparse
    _backend_host = urlparse(BACKEND_BASE_URL).netloc or BACKEND_BASE_URL
    if _backend_host and _backend_host not in _allowed and '*' not in _allowed:
        _allowed.append(_backend_host)
ALLOWED_HOSTS = _allowed

APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv(
    'APPLICATIONINSIGHTS_CONNECTION_STRING',
    'InstrumentationKey=00000000-0000-0000-0000-000000000000'
)

# OpenTelemetry is initialized in apis/otel.py based on APPLICATIONINSIGHTS_CONNECTION_STRING

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apis.infrastructure.middleware': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Logging for feedback analysis services (detailed debugging)
        'apis.app': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'feedback_analysis': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'feedback_analysis.services': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # ML Pipeline logging (detailed debugging for local ML services)
        'feedback_analysis.services.ml': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'feedback_analysis.services.ml.embedding_service': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'feedback_analysis.services.ml.local_sentiment_service': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'feedback_analysis.services.ml.local_processing_service': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apis.prompts': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Celery logging
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery.task': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Suppress verbose Azure SDK logging
        'azure': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'azure.core.pipeline.policies.http_logging_policy': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Cosmos DB Configuration
COSMOS_DB_CONFIG = {
    'endpoint': os.getenv('COSMOS_DB_ENDPOINT', 'https://your-cosmos-account.documents.azure.com:443/'),
    'key': os.getenv('COSMOS_DB_KEY', 'your-cosmos-db-key'),
    'database_name': os.getenv('COSMOS_DB_DATABASE', 'saramsa-db'),
    'containers': {
        'users': os.getenv('COSMOS_DB_USERS_CONTAINER', 'users'),
        'analysis': os.getenv('COSMOS_DB_ANALYSIS_CONTAINER', 'analysis'),
        'uploads': os.getenv('COSMOS_DB_UPLOADS_CONTAINER', 'uploads'),
        'user_stories': os.getenv('COSMOS_DB_USER_STORIES_CONTAINER', 'user_stories'),
        'projects': os.getenv('COSMOS_DB_PROJECTS_CONTAINER', 'projects'),
        'user_data': os.getenv('COSMOS_DB_USER_DATA_CONTAINER', 'user_data'),
        'integrations': os.getenv('COSMOS_DB_INTEGRATIONS_CONTAINER', 'integrations'),
        'password_resets': os.getenv('COSMOS_DB_PASSWORD_RESETS_CONTAINER', 'password_resets'),
        'insights': os.getenv('COSMOS_DB_INSIGHTS_CONTAINER', 'insights'),
        'comment_extractions': os.getenv('COSMOS_DB_COMMENT_EXTRACTIONS_CONTAINER', 'comment_extractions'),
        'taxonomies': os.getenv('COSMOS_DB_TAXONOMIES_CONTAINER', 'taxonomies'),
        'usage': os.getenv('COSMOS_DB_USAGE_CONTAINER', 'usage'),
        'insight_rules': os.getenv('COSMOS_DB_INSIGHT_RULES_CONTAINER', 'insight_rules'),
        'insight_reviews': os.getenv('COSMOS_DB_INSIGHT_REVIEWS_CONTAINER', 'insight_reviews'),
        'work_item_quality_rules': os.getenv('COSMOS_DB_WORK_ITEM_QUALITY_RULES_CONTAINER', 'work_item_quality_rules'),
        'ingestion_schedules': os.getenv('COSMOS_DB_INGESTION_SCHEDULES_CONTAINER', 'ingestion_schedules'),
        'project_roles': os.getenv('COSMOS_DB_PROJECT_ROLES_CONTAINER', 'project_roles'),
        'registration_otps': os.getenv('COSMOS_DB_REGISTRATION_OTPS_CONTAINER', 'registration_otps'),
    } 
}


# Celery Configuration - Azure Redis
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')  # Required for Azure Redis Cache
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')  # Required for Azure Redis Cache

# Add SSL certificate requirements to Redis URLs for Azure Redis
if CELERY_BROKER_URL and CELERY_BROKER_URL.startswith('rediss://'):
    # Append ssl_cert_reqs parameter to URL if not already present
    if 'ssl_cert_reqs' not in CELERY_BROKER_URL:
        separator = '&' if '?' in CELERY_BROKER_URL else '?'
        # Use CERT_NONE as the value (required by Celery Redis backend)
        CELERY_BROKER_URL = f"{CELERY_BROKER_URL}{separator}ssl_cert_reqs=CERT_NONE"
        # Update environment variable for celery.py
        os.environ['CELERY_BROKER_URL'] = CELERY_BROKER_URL
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        'ssl_cert_reqs': ssl.CERT_NONE,  # Azure Redis uses CERT_NONE
    }
else:
    CELERY_BROKER_TRANSPORT_OPTIONS = {}

if CELERY_RESULT_BACKEND and CELERY_RESULT_BACKEND.startswith('rediss://'):
    # Append ssl_cert_reqs parameter to URL if not already present
    if 'ssl_cert_reqs' not in CELERY_RESULT_BACKEND:
        separator = '&' if '?' in CELERY_RESULT_BACKEND else '?'
        # Use CERT_NONE as the value (required by Celery Redis backend)
        CELERY_RESULT_BACKEND = f"{CELERY_RESULT_BACKEND}{separator}ssl_cert_reqs=CERT_NONE"
        # Update environment variable for celery.py
        os.environ['CELERY_RESULT_BACKEND'] = CELERY_RESULT_BACKEND
    CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {
        'ssl_cert_reqs': ssl.CERT_NONE,  # Azure Redis uses CERT_NONE
    }
else:
    CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {}

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

DATABASES = {}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'aiCore',
    'feedback_analysis',
    'work_items',
    'corsheaders',
    'authentication',
    'integrations',
]

# Custom authentication backend for Cosmos DB
AUTHENTICATION_BACKENDS = [
    'authentication.authentication.CosmosDBAuthenticationBackend',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom logging middleware
    'apis.infrastructure.middleware.RequestResponseLoggingMiddleware',
    'apis.infrastructure.performance_middleware.PerformanceTrackingMiddleware',
    'apis.infrastructure.performance_middleware.DatabaseQueryCountMiddleware',
    'apis.infrastructure.middleware.SecurityLoggingMiddleware',
]

ROOT_URLCONF = 'apis.urls'
APPEND_SLASH = False

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'apis.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

# Password validation disabled - using custom Cosmos DB authentication
# AUTH_PASSWORD_VALIDATORS = []


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
# Cosmos DB is used for all data storage - no Django models needed

CORS_ALLOW_ALL_ORIGINS = False

# Optional: Allow cookies (if using session/auth)
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    'https://saramsa-fe.azurewebsites.net',
    'https://mango-pebble-0a60bb60f.3.azurestaticapps.net',
    'https://saramsa-chi.vercel.app',
    'https://saramsa-r4pmpubsw-rakeshmahendrans-projects.vercel.app',
    'http://localhost:3000',
    'http://localhost:3001',
    'http://localhost:8000',
    'http://localhost',
]
# Extra CORS origins from env (comma-separated), e.g. production frontend URL
_cors_extra = os.getenv('CORS_EXTRA_ORIGINS', '')
if _cors_extra:
    CORS_ALLOWED_ORIGINS = list(CORS_ALLOWED_ORIGINS) + [o.strip() for o in _cors_extra.split(',') if o.strip()]

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]

CORS_ALLOW_HEADERS = [
    'Accept',
    'Content-Type',
    'Authorization',
    'X-Requested-With',
    'X-CSRFToken',
    'Origin',
    'Referer',
]

# Trust requests coming from the static frontend domain (needed for some POSTs)
CSRF_TRUSTED_ORIGINS = [
    'https://saramsa-fe.azurewebsites.net',
    'https://mango-pebble-0a60bb60f.3.azurestaticapps.net',
    'https://saramsa-chi.vercel.app',
    'https://saramsa-r4pmpubsw-rakeshmahendrans-projects.vercel.app',
    'http://localhost:3000',
    'http://localhost:3001',
    'http://localhost:8000',
    'http://localhost',
]
# Extra CSRF origins from env (comma-separated), e.g. production frontend URL
_csrf_extra = os.getenv('CSRF_EXTRA_ORIGINS', '')
if _csrf_extra:
    CSRF_TRUSTED_ORIGINS = list(CSRF_TRUSTED_ORIGINS) + [o.strip() for o in _csrf_extra.split(',') if o.strip()]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'authentication.authentication.CosmosDBJWTAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # Fallback
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apis.core.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # 1 hour access token
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),    # Longer-lived refresh token
    'AUTH_HEADER_TYPES': ('Bearer',),
    'UPDATE_LAST_LOGIN': True,
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(hours=1),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}


# Performance Configuration
SLOW_REQUEST_THRESHOLD = float(os.getenv('SLOW_REQUEST_THRESHOLD', '2.0'))  # seconds
VERY_SLOW_REQUEST_THRESHOLD = float(os.getenv('VERY_SLOW_REQUEST_THRESHOLD', '5.0'))  # seconds

REDIS_URL = os.getenv('REDIS_URL')  

# Cosmos DB Performance Configuration
COSMOS_CONNECTION_POOL_SIZE = int(os.getenv('COSMOS_CONNECTION_POOL_SIZE', '10'))
COSMOS_REQUEST_TIMEOUT = int(os.getenv('COSMOS_REQUEST_TIMEOUT', '30'))
COSMOS_RETRY_TOTAL = int(os.getenv('COSMOS_RETRY_TOTAL', '3'))

# Local ML Pipeline Configuration
USE_LOCAL_PIPELINE = os.getenv('USE_LOCAL_PIPELINE', 'false').lower() == 'true'
AZURE_DEVOPS_ORGANIZATION = os.getenv('AZURE_DEVOPS_ORGANIZATION')
AZURE_DEVOPS_PROJECT = os.getenv('AZURE_DEVOPS_PROJECT')
AZURE_DEVOPS_PAT = os.getenv('AZURE_DEVOPS_PAT')

# Jira Configuration - Optional, but required if using Jira
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY')
JIRA_DOMAIN = os.getenv('JIRA_DOMAIN')

# Swagger/OpenAPI Configuration
SPECTACULAR_SETTINGS = {
    'TITLE': 'Saramsa API',
    'DESCRIPTION': 'API documentation for Saramsa application',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'SECURITY': [
        {
            'Bearer': []
        }
    ],
    'TAGS': [
        {'name': 'auth', 'description': 'Authentication endpoints'},
        {'name': 'insights', 'description': 'Insights generation endpoints'},
        {'name': 'workitems', 'description': 'DevOps work items endpoints'},
        {'name': 'upload', 'description': 'File upload endpoints'},
    ],
}

# Email configuration (password reset + registration OTP)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND') or (
    'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@saramsa.ai')
PASSWORD_RESET_FROM_EMAIL = os.getenv('PASSWORD_RESET_FROM_EMAIL', DEFAULT_FROM_EMAIL)
PASSWORD_RESET_EMAIL_SUBJECT = os.getenv('PASSWORD_RESET_EMAIL_SUBJECT', 'Reset your Saramsa password')
REGISTRATION_OTP_EMAIL_SUBJECT = os.getenv('REGISTRATION_OTP_EMAIL_SUBJECT', 'Your Saramsa registration code')
REGISTRATION_OTP_TTL_MINUTES = int(os.getenv('REGISTRATION_OTP_TTL_MINUTES', '10'))
REGISTRATION_OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv('REGISTRATION_OTP_RESEND_COOLDOWN_SECONDS', '60'))
REGISTRATION_OTP_MAX_ATTEMPTS = int(os.getenv('REGISTRATION_OTP_MAX_ATTEMPTS', '5'))
