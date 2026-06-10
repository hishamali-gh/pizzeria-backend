import os

from dotenv import load_dotenv

from pathlib import Path

from datetime import timedelta


# ENVIRONMENT CONFIG.
# We don't need 'django-environ' since we are using Docker as well.
# The native method, 'os.environ.get' will work with the bi-flow setup.
env = os.environ.get

# Load environment variables from the .env file in your project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# CORE DJANGO APPLICATION CONFIG.
SECRET_KEY = env('SECRET_KEY')

if not SECRET_KEY:
    raise ValueError("CRITICAL SECURITY ERROR: The SECRET_KEY environment variable is not set!")

DEBUG = bool(env('DEBUG', default=False))

ALLOWED_HOSTS = ['.localhost', '127.0.0.1', 'localhost']

ROOT_URLCONF = 'pizzeria_backend.urls' # Private URLs
PUBLIC_SCHEMA_URLCONF = 'pizzeria_backend.urls_public' # Public URLs

WSGI_APPLICATION = 'pizzeria_backend.wsgi.application'

# This configuration enables the project to handle ASGI data stream.
ASGI_APPLICATION = 'pizzeria_backend.asgi.application' # Step 1. Next step is in 'asgi.py'


# TENANT CONFIG.
TENANT_MODEL = 'tenants.Tenant'
TENANT_DOMAIN_MODEL = 'tenants.Domain'


# APPS CONFIG.
# Defining 'SHARED' and 'TENANT' applications separately to handle the Django-Tenants workflow
SHARED_APPS = [
    'daphne', # ASGI Server for Django-Channels
    'channels',

    'django_tenants',

    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    
    'rest_framework',

    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',

    'corsheaders',

    'accounts',
    'tenants',
    'billing',

    'django_celery_beat'
]

TENANT_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.admin',

    'employees',
    'devices'
]

INSTALLED_APPS = SHARED_APPS + [app for app in TENANT_APPS if app not in SHARED_APPS]


# MIDDLEWARES CONFIG.
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django_tenants.middleware.main.TenantMainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# TEMPLATES CONFIG.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# DATABASE CONFIG.
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': env('DB_NAME', default='pizzeria_db'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='development_password'),
        'HOST': env('DB_HOST', default='127.0.0.1'),
        'PORT': env('DB_PORT', default='5432')
    }
}

DATABASE_ROUTERS = ('django_tenants.routers.TenantSyncRouter',)


# AUTHENTICATION CONFIG.
AUTH_USER_MODEL = 'accounts.User'

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


# DRF CONFIG.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication'
    ]
}


# JWT CONFIG.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=12),

    'AUTH_HEADER_TYPES': ['Bearer'],
    'AUTH_COOKIE': 'access', # Matches the 'response.set_cookie' key
    'AUTH_COOKIE_REFRESH': 'refresh', # Matches the 'response.set_cookie' key
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_PATH': '/',
    'AUTH_COOKIE_SAMESITE': 'Lax',
}


# CORS & CSRF CONFIG.
# The industrial permission list
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]

# Allow all subdomains
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^http://.*\.localhost:5173$',
]

# Allow credentials (cookies/MFA tokens) to pass through
CORS_ALLOW_CREDENTIALS = True

# CORS_ALLOW_ALL_ORIGINS = True # Temporary setup for quick debugging

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
    'http://*.localhost:5173',
]


# INTERNATIONALIZATION CONFIG.
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# STATIC FILES CONFIG.
STATIC_URL = '/static/'

BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# EMAIL CONFIG.
# Swaps Django's internal compiler from 'console' to the native networking network handler
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Target mail server hostname and transmission gateway port
EMAIL_HOST = env('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = int(env('EMAIL_PORT', default=587)) # TLS Port

# Safety Handshaking (Strictly use TLS encryption layers)
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

# Authentication Access Handshake Keys
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# Sender Label displayed to operators on the manufacturing floor
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='pizzeria@localhost')


# RAZORPAY CONFIG.
RAZORPAY_KEY_ID = env('RAZORPAY_KEY_ID', default='')
RAZORPAY_KEY_SECRET = env('RAZORPAY_KEY_SECRET', default='')


# REDIS CONFIG.
REDIS_URL = env('REDIS_URL', default='redis://127.0.0.1:6379/0')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}


# CELERY CONFIG.
# Pointing to database index '1' so it doesn't conflict with Channels (usually on db=0)
CELERY_BROKER_URL = f'{REDIS_URL}/1'
CELERY_RESULT_BACKEND = f'{REDIS_URL}/1'

# Timezone matching your standard localization
CELERY_TIMEZONE = 'UTC'

# Explicitly use django-celery-beat for handling our bimonthly checkups
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
