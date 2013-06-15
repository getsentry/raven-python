"""
raven.conf.defaults
~~~~~~~~~~~~~~~~~~~

Represents the default values for all Sentry settings.

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import os
import os.path
import socket

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))

# This should be the full URL to sentries store view
SERVERS = None

TIMEOUT = 1

# TODO: this is specific to Django
CLIENT = 'raven.contrib.django.DjangoClient'

# Not all environments have access to socket module, for example Google App Engine
# Need to check to see if the socket module has ``gethostname``, if it doesn't we
# will set it to None and require it passed in to ``Client`` on initializtion.
NAME = socket.gethostname() if hasattr(socket, 'gethostname') else None

# Superuser key -- will be used if set, otherwise defers to
# SECRET_KEY and PUBLIC_KEY
KEY = None

# Credentials to authenticate with the Sentry server
SECRET_KEY = None
PUBLIC_KEY = None

# We allow setting the site name either by explicitly setting it with the
# SENTRY_SITE setting, or using the django.contrib.sites framework for
# fetching the current site. Since we can't reliably query the database
# from this module, the specific logic is within the SiteFilter
SITE = None

# The maximum number of elements to store for a list-like structure.
MAX_LENGTH_LIST = 50

# The maximum length to store of a string-like structure.
MAX_LENGTH_STRING = 400

# Automatically log frame stacks from all ``logging`` messages.
AUTO_LOG_STACKS = False

# Client-side data processors to apply
PROCESSORS = (
    'raven.processors.SanitizePasswordsProcessor',
)

# Default Project ID
PROJECT = 1
