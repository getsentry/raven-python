#!/usr/bin/env python
import logging
import sys
from os.path import dirname, abspath, join, splitext
from os import listdir
from optparse import OptionParser

where_am_i = dirname(abspath(__file__))

logging.getLogger('sentry').addHandler(logging.StreamHandler())


from django.conf import settings

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
        CELERY_ALWAYS_EAGER=True,
        TEMPLATE_DEBUG=True,
        TEMPLATE_DIRS=[join(where_am_i, 'tests', 'contrib', 'django', 'templates')],
    )
    import djcelery
    djcelery.setup_loader()
