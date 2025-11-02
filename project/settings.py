"""
Django settings for the NLP Chat project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file in BASE_DIR
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Fallback: try loading from current directory
    load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY') or 'django-insecure-dev-key-change-in-production-pln-an-na-cesar-evily-2024'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

# MongoDB settings
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')

# Django default database (sqlite) - required so management commands / migrations work.
# We still use MongoDB for chat persistence via PyMongo, but Django expects a DATABASES setting.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'app' / 'static',
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Hugging Face settings
HF_MODEL_NAME = os.getenv('HF_MODEL_NAME')
HF_API_TOKEN = os.getenv('HF_API_TOKEN')
HF_INFERENCE_MODEL = os.getenv('HF_INFERENCE_MODEL', 'gpt-5-mini')
# If True, always use the Hugging Face Inference API (HF_INFERENCE_MODEL) instead of local model
USE_HF_FOR_ALL = os.getenv('USE_HF_FOR_ALL', 'False') == 'True'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'app': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
# When running in DEBUG mode, enable console logging and set app logger to DEBUG
if DEBUG:
    LOGGING.setdefault('handlers', {})
    LOGGING['handlers']['console'] = {
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
        'formatter': 'verbose',
    }
    LOGGING.setdefault('loggers', {})
    LOGGING['loggers'].setdefault('app', {})
    LOGGING['loggers']['app']['handlers'] = ['file', 'console']
    LOGGING['loggers']['app']['level'] = 'DEBUG'
    LOGGING['loggers'].setdefault('django', {})
    # show Django INFO+ on console during DEBUG for easier troubleshooting
    LOGGING['loggers']['django']['handlers'] = ['file', 'console']
    LOGGING['loggers']['django']['level'] = 'DEBUG'