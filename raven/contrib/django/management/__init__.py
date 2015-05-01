"""
raven.contrib.django.raven.management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2013 by the Sentry Team, see AUTHORS for more details
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import, print_function

import sys
import warnings

from functools import wraps


def patch_cli_runner():
    """
    Patches ``cls.execute``, returning a boolean describing if the
    attempt was successful.
    """
    try:
        from django.core.management.base import BaseCommand
    except ImportError:
        warnings.warn('Unable to patch Django management commands')
        return
    else:
        cls = BaseCommand

    try:
        original_func = cls.execute
    except AttributeError:
        # must not be a capable version of Django
        return False

    if hasattr(original_func, '__raven_patched'):
        return False

    @wraps(original_func)
    def new_execute(self, *args, **kwargs):
        try:
            return original_func(self, *args, **kwargs)
        except Exception:
            from raven.contrib.django.models import client

            client.captureException(extra={
                'argv': sys.argv
            })
            raise

    new_execute.__raven_patched = True
    cls.execute = new_execute

    return True
