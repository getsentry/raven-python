from __future__ import absolute_import

import os.path
import pytest
import sys

collect_ignore = []
if sys.version_info[0] > 2:
    if sys.version_info[1] < 3:
        collect_ignore.append('tests/contrib/flask')
    if sys.version_info[1] == 2:
        collect_ignore.append('tests/handlers/logbook')

try:
    import gevent  # NOQA
except ImportError:
    collect_ignore.append('tests/transport/gevent')

try:
    import web  # NOQA
except ImportError:
    collect_ignore.append('tests/contrib/webpy')

try:
    import django  # NOQA
except ImportError:
    django = None
    collect_ignore.append('tests/contrib/django')

try:
    import tastypie  # NOQA
except ImportError:
    collect_ignore.append('tests/contrib/django/test_tastypie.py')


INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',

    'raven.contrib.django',
    'tests.contrib.django',
]


use_djcelery = True
try:
    import djcelery  # NOQA
    INSTALLED_APPS.append('djcelery')
except ImportError:
    use_djcelery = False


def configure_django(project_root):
    from django.conf import settings

    settings.configure(
        DATABASE_ENGINE='sqlite3',
        DATABASES={
            'default': {
                'NAME': ':memory:',
                'ENGINE': 'django.db.backends.sqlite3',
                'TEST_NAME': ':memory:',
            },
        },
        DATABASE_NAME=':memory:',
        TEST_DATABASE_NAME=':memory:',
        INSTALLED_APPS=INSTALLED_APPS,
        ROOT_URLCONF='tests.contrib.django.urls',
        DEBUG=False,
        SITE_ID=1,
        BROKER_HOST="localhost",
        BROKER_PORT=5672,
        BROKER_USER="guest",
        BROKER_PASSWORD="guest",
        BROKER_VHOST="/",
        SENTRY_ALLOW_ORIGIN='*',
        CELERY_ALWAYS_EAGER=True,
        TEMPLATE_DEBUG=True,
        LANGUAGE_CODE='en',
        LANGUAGES=(('en', 'English'),),
        TEMPLATE_DIRS=[
            os.path.join(project_root, 'tests', 'contrib', 'django', 'templates'),
        ],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
            'DIRS': [
                os.path.join(project_root, 'tests', 'contrib', 'django', 'templates'),
            ],
        }],
        ALLOWED_HOSTS=['*'],
        DISABLE_SENTRY_INSTRUMENTATION=True,
        SENTRY_CLIENT='tests.contrib.django.tests.MockClient'
    )


def pytest_configure(config):
    if django:
        configure_django(os.path.dirname(os.path.abspath(__file__)))


def pytest_runtest_teardown(item):
    if django:
        from raven.contrib.django.models import client
        client.events = []


@pytest.fixture
def project_root():
    return os.path.dirname(os.path.abspath(__file__))
