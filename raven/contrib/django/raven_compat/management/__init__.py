"""
raven.contrib.django.raven_compat.management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2013 by the Sentry Team, see AUTHORS for more details
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import, print_function

from raven.contrib.django.management import *  # NOQA

import warnings

warnings.warn('raven.contrib.django.raven_compat is deprecated. Use raven_django instead.', DeprecationWarning)
