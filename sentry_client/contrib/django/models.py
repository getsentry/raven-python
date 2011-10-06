"""
sentry_client.contrib.django.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Acts as an implicit hook for Django installs.

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import sys
import logging
import warnings

from django.core.signals import got_request_exception
from django.conf import settings as django_settings
from django.utils.hashcompat import md5_constructor

from sentry_client.conf import settings

logger = logging.getLogger('sentry.errors.client')

_client = (None, None)
def get_client():
    global _client
    if _client[0] != settings.CLIENT:
        module, class_name = settings.CLIENT.rsplit('.', 1)
        _client = (settings.CLIENT, getattr(__import__(module, {}, {}, class_name), class_name)())
    return _client[1]
client = get_client()

def get_installed_apps():
    """
    Generate a list of modules in settings.INSTALLED_APPS.
    """
    out = set()
    for app in django_settings.INSTALLED_APPS:
        out.add(app)
    return out

def configure_settings():
    # Some sane overrides to better mix with Django
    values = {}
    for k in (k for k in dir(django_settings) if k.startswith('SENTRY_')):
        print k, values
        values[k.split('SENTRY_', 1)[1]] = getattr(django_settings, k)

    if 'KEY' not in values:
        values['KEY'] = md5_constructor(django_settings.SECRET_KEY).hexdigest()
    if 'DEBUG' not in values:
        values['DEBUG'] = django_settings.DEBUG

    if 'REMOTE_URL' in values:
        v = values['REMOTE_URL']
        if isinstance(v, basestring):
            values['REMOTE_URL'] = [v]
        elif not isinstance(v, (list, tuple)):
            raise ValueError("Sentry setting 'REMOTE_URL' must be of type list.")

    if 'INCLUDE_PATHS' not in values:
        values['INCLUDE_PATHS'] = get_installed_apps()
    else:
        values['INCLUDE_PATHS'] = set(values['INCLUDE_PATHS']) + get_installed_apps()

    settings.configure(**values)

configure_settings()

if settings.REMOTE_URL:
    class MockTransaction(object):
        def commit_on_success(self, func):
            return func

        def is_dirty(self):
            return False

        def rollback(self):
            pass

    transaction = MockTransaction()
else:
    from django.db import transaction

@transaction.commit_on_success
def sentry_exception_handler(request=None, **kwargs):
    exc_info = sys.exc_info()
    try:

        if django_settings.DEBUG or getattr(exc_info[0], 'skip_sentry', False):
            return

        if transaction.is_dirty():
            transaction.rollback()

        extra = dict(
            request=request,
        )

        get_client().create_from_exception(**extra)
    except Exception, exc:
        try:
            logger.exception(u'Unable to process log entry: %s' % (exc,))
        except Exception, exc:
            warnings.warn(u'Unable to process log entry: %s' % (exc,))
    finally:
        del exc_info

got_request_exception.connect(sentry_exception_handler)

