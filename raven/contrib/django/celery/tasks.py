"""
raven.contrib.django.celery.tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.contrib.django.models import client  # NOQA

import warnings

warnings.warn('raven.contrib.django is deprecated. Use raven_django instead.', DeprecationWarning)
