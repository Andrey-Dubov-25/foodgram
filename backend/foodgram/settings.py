import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-@&3s300i-z-wi7q9*n^-6x4@ygo!t+8i*m2@9*x$zd&nxb22%u'

DEBUG = True

ALLOWED_HOSTS = ['foodgram.serveblog.net', '158.160.209.12', 'localhost', '127.0.0.1']

CSRF_TRUSTED_ORIGINS = ['https://foodgram.serveblog.net', 'http://foodgram.serveblog.net']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

AUTH_USER_MODEL = 'users.MyUser'


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'recipe.apps.RecipeConfig',
    'rest_framework',
    'rest_framework.authtoken',
    'core.apps.CoreConfig',
    'users.apps.UsersConfig',
    'api.apps.ApiConfig',
    'debug_toolbar',
    'django_filters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = [
    '127.0.0.1'
]

ROOT_URLCONF = 'foodgram.urls'

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

WSGI_APPLICATION = 'foodgram.wsgi.application'

# DATABASES = {
#     'default': {
#         # Меняем настройку Django: теперь для работы будет использоваться
#         # бэкенд postgresql
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('POSTGRES_DB', 'django'),
#         'USER': os.getenv('POSTGRES_USER', 'django'),
#         'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
#         'HOST': os.getenv('DB_HOST', ''),
#         'PORT': os.getenv('DB_PORT', 5432)
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': '/data/db.sqlite3',
#     }
# } 

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


LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'collected_static'


MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'

# EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'


REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 6,
}

DJOSER = {
    'LOGIN_FIELD': 'email',
    'HIDE_USERS': False,
    'SERIALIZERS': {
        'user': 'api.serializers.UserSerializer',
        'token_create': 'api.serializers.GetTokenSerializer',
    },
    'PERMISSIONS': {
        'user_list': ['rest_framework.permissions.AllowAny'],
        'user': ['djoser.permissions.CurrentUserOrAdminOrReadOnly'],
    }
}
