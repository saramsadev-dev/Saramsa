from pathlib import Path
import os
import ssl
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# Ensure the logs directory exists before LOGGING handlers try to write files
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-your-secret-key-here-change-in-production')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Allow all Azure Web App hostnames and localhost
ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS',
    '.azurewebsites.net,127.0.0.1,localhost'
).split(',')
# Ensure .azurewebsites.net is always included for Azure deployments
if '.azurewebsites.net' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('.azurewebsites.net')

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
    }
}

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# SSL configuration for Redis (if using rediss://)
if CELERY_BROKER_URL.startswith('rediss://'):
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        'ssl_cert_reqs': ssl.CERT_REQUIRED,
    }
    CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {
        'ssl_cert_reqs': ssl.CERT_REQUIRED,
    }
else:
    CELERY_BROKER_TRANSPORT_OPTIONS = {}
    CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {}

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Cosmos DB Only - No traditional SQL database needed
# Django apps that require database models are disabled
# All data storage is handled through Cosmos DB service
DATABASES = {}

# Application definition

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
    'https://mango-pebble-0a60bb60f.3.azurestaticapps.net',
    'https://saramsa-chi.vercel.app',
    'http://localhost:3000',      
    'http://localhost:8000',   
]

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
    'https://mango-pebble-0a60bb60f.3.azurestaticapps.net',
    'https://saramsa-chi.vercel.app',
    'http://localhost:3000',
    'http://localhost:8000',
]

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

# Redis Configuration for Caching
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Cosmos DB Performance Configuration
COSMOS_CONNECTION_POOL_SIZE = int(os.getenv('COSMOS_CONNECTION_POOL_SIZE', '10'))
COSMOS_REQUEST_TIMEOUT = int(os.getenv('COSMOS_REQUEST_TIMEOUT', '30'))
COSMOS_RETRY_TOTAL = int(os.getenv('COSMOS_RETRY_TOTAL', '3'))
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