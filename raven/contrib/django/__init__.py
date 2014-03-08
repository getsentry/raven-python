"""
raven.contrib.django
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

# Importing just to register the Django specific Exception handler
from .events import Exception  # NOQA
del Exception  # NOQA

from .client import DjangoClient  # NOQA
