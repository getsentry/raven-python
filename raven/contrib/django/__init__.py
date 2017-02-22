"""
raven.contrib.django
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import django

default_app_config = 'raven.contrib.django.apps.RavenConfig'

from .client import DjangoClient  # NOQA

# Django 1.8 uses ``raven.contrib.apps.RavenConfig``
if django.VERSION < (1, 7, 0):
    from .models import initialize
    initialize()
