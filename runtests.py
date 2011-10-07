#!/usr/bin/env python
import logging
import sys
from os.path import dirname, abspath, join
from optparse import OptionParser

where_am_i = dirname(abspath(__file__))

sys.path.insert(0, where_am_i)

logging.getLogger('sentry').addHandler(logging.StreamHandler())

from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASE_ENGINE='sqlite3',
        DATABASES={
            'default': {
                'ENGINE': 'sqlite3',
                'TEST_NAME': 'sentry_tests.db',
            },
        },
        # HACK: this fixes our threaded runserver remote tests
        # DATABASE_NAME='test_sentry',
        TEST_DATABASE_NAME='sentry_tests.db',
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.sessions',
            'django.contrib.sites',

            # Included to fix Disqus' test Django which solves IntegrityMessage case
            'django.contrib.contenttypes',

            'djcelery', # celery client

            'sentry_client.contrib.django',
        ],
        ROOT_URLCONF='',
        DEBUG=False,
        SITE_ID=1,
        BROKER_HOST="localhost",
        BROKER_PORT=5672,
        BROKER_USER="guest",
        BROKER_PASSWORD="guest",
        BROKER_VHOST="/",
        CELERY_ALWAYS_EAGER=True,
        TEMPLATE_DEBUG=True,
        TEMPLATE_DIRS=[join(where_am_i, 'tests', 'contrib', 'django', 'templates')],
    )
    import djcelery
    djcelery.setup_loader()

from django_nose import NoseTestSuiteRunner

def runtests(*test_args, **kwargs):
    if not test_args:
        test_args = ['tests']

    test_runner = NoseTestSuiteRunner(**kwargs)

    failures = test_runner.run_tests(test_args)
    sys.exit(failures)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--verbosity', dest='verbosity', action='store', default=1, type=int)
    parser.add_options(NoseTestSuiteRunner.options)
    (options, args) = parser.parse_args()

    runtests(*args, **options.__dict__)