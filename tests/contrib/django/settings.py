
import os

# ---- SENTRY CONFIG ---- #
SENTRY_CLIENT = 'tests.contrib.django.tests.MockClient'
DISABLE_SENTRY_INSTRUMENTATION = True
SENTRY_ALLOW_ORIGIN = '*'

# ---- GENERIC DJANGO SETTINGS ---- #
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = "Change this!"
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',

    'raven.contrib.django',
    'tests.contrib.django',
]


DATABASE_ENGINE='sqlite3'
DATABASES = {
    'default': {
        'NAME': ':memory:',
        'ENGINE': 'django.db.backends.sqlite3',
        'TEST_NAME': ':memory:',
    },
}
DATABASE_NAME = ':memory:'
TEST_DATABASE_NAME = ':memory:'
ROOT_URLCONF = 'tests.contrib.django.urls'
DEBUG = False
SITE_ID = 1

TEMPLATE_DEBUG = True
LANGUAGE_CODE = 'en'
LANGUAGES = (('en', 'English'),)
TEMPLATE_DIRS = [
    os.path.join(PROJECT_ROOT, 'templates'),
]
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
    'DIRS': TEMPLATE_DIRS,
}]
ALLOWED_HOSTS = ['*']

# ---- CELERY SETTINGS ---- #

try:
    import djcelery  # NOQA
    INSTALLED_APPS.append('djcelery')
except ImportError:
    pass

BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "guest"
BROKER_PASSWORD = "guest"
BROKER_VHOST = "/"
CELERY_ALWAYS_EAGER = True
