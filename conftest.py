from django.conf import settings
import os.path
import sys
collect_ignore = []
if sys.version_info[0] > 2:
    collect_ignore.append("tests/contrib/flask")
    collect_ignore.append("tests/handlers/logbook")

INSTALLED_APPS=[
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.sites',

    # Included to fix Disqus' test Django which solves IntegrityMessage case
    'django.contrib.contenttypes',

    'raven.contrib.django',
]


use_djcelery = True
try:
    import djcelery
    INSTALLED_APPS.append('djcelery')
except ImportError:
    use_djcelery = False


def pytest_configure(config):
    where_am_i = os.path.dirname(os.path.abspath(__file__))

    if not settings.configured:
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
            ROOT_URLCONF='',
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
            TEMPLATE_DIRS=[os.path.join(where_am_i, 'tests', 'contrib', 'django', 'templates')],
            ALLOWED_HOSTS=['*'],
        )
