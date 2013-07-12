"""
raven.utils.testutils
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2013 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from exam import Exam

from .compat import TestCase as BaseTestCase


class TestCase(Exam, BaseTestCase):
    pass
