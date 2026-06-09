from pathlib import Path
import os
from dotenv import load_dotenv
try:
    import dj_database_url
    _HAS_DJ_DB_URL = True
except ImportError:
    _HAS_DJ_DB_URL = False

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-shuttlesplit-v2-secret-key-2024')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

try:
    import whitenoise  # noqa
    _HAS_WHITENOISE = True
except ImportError:
    _HAS_WHITENOISE = False

try:
    import rest_framework  # noqa
    _HAS_DRF = True
except ImportError:
    _HAS_DRF = False

try:
    import corsheaders  # noqa
    _HAS_CORS = True
except ImportError:
    _HAS_CORS = False

INSTALLED_APPS = [
    *(['whitenoise.runserver_nostatic'] if _HAS_WHITENOISE else []),
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    *(['rest_framework', 'rest_framework.authtoken'] if _HAS_DRF else []),
    *(['corsheaders'] if _HAS_CORS else []),
    'accounts',
    'groups',
    'sessions_app',
    'wallet',
    'payments',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    *(['whitenoise.middleware.WhiteNoiseMiddleware'] if _HAS_WHITENOISE else []),
    *(['corsheaders.middleware.CorsMiddleware'] if _HAS_CORS else []),
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

WSGI_APPLICATION = 'config.wsgi.application'

# Database — SQLite locally, PostgreSQL on Railway (via DATABASE_URL)
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and _HAS_DJ_DB_URL:
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'accounts.User'
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
}

# Celery
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_TIMEZONE = 'Asia/Ho_Chi_Minh'
CELERY_BEAT_SCHEDULE = {
    'send-debt-reminders': {
        'task': 'notifications.tasks.send_debt_reminders',
        'schedule': 86400,  # daily
    },
}

# Email
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'ShuttleSplit <noreply@shuttlesplit.vn>')

# Business rules
DEBT_REMINDER_THRESHOLD = 200000  # 200k VND
DEBT_REMINDER_DAYS = 30

CORS_ALLOW_ALL_ORIGINS = True
