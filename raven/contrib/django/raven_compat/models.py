"""
raven.contrib.django.raven_compat.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

from raven.contrib.django.models import *  # NOQA

import warnings

warnings.warn('raven.contrib.django.raven_compat is deprecated. Use raven_django instead.', DeprecationWarning)
