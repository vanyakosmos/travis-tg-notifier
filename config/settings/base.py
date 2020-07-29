import os
from os import getenv
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url

BASE_DIR = str(Path(os.path.abspath(__file__)).parents[2])

SECRET_KEY = getenv('SECRET_KEY')
DEBUG = getenv('DEBUG', '0') == '1'

APP_URL = getenv('APP_URL')
ALLOWED_HOSTS = []
if APP_URL:
    APP_URL = APP_URL.strip('/')
    host = urlparse(APP_URL).netloc
    ALLOWED_HOSTS.append(host)
if DEBUG:
    ALLOWED_HOSTS.append('localhost')
AUTH_USER_MODEL = 'core.User'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    # local
    'core.apps.CoreConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASE_URL = getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/travis_tg_notifier',
)
DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

LOGGING_LEVEL = getenv('LOGGING_LEVEL', 'DEBUG')
LOGGING_LEVEL_ROOT = getenv('LOGGING_LEVEL_ROOT', 'INFO')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': f'[%(asctime)s] %(levelname)s %(name)27s:%(lineno)-3d > %(message)s',
            'datefmt': "%Y/%m/%d %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': LOGGING_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        module: {
            'handlers': ['console'],
            'level': LOGGING_LEVEL,
            'propagate': False,
        }
        for module in ['core']
    },
    'root': {
        'handlers': ['console'],
        'level': LOGGING_LEVEL_ROOT,
        'propagate': False,
    },
}

TELEGRAM_BOT_TOKEN = getenv('TELEGRAM_BOT_TOKEN')
if APP_URL:
    WEBHOOK_URL = '/'.join([APP_URL, 'webhook', TELEGRAM_BOT_TOKEN])
else:
    WEBHOOK_URL = None
CHECK_SIGNATURE = getenv('CHECK_SIGNATURE', '1') == '1'
