from django.conf import settings
import os.path


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
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.admin',
                'django.contrib.sessions',
                'django.contrib.sites',

                # Included to fix Disqus' test Django which solves IntegrityMessage case
                'django.contrib.contenttypes',

                'djcelery',  # celery client

                'raven.contrib.django',
            ],
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
        )
        import djcelery
        djcelery.setup_loader()
