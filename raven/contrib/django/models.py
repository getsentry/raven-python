"""
raven.contrib.django.models
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

logger = logging.getLogger('sentry.errors.client')


def get_installed_apps():
    """
    Generate a list of modules in settings.INSTALLED_APPS.
    """
    out = set()
    for app in django_settings.INSTALLED_APPS:
        out.add(app)
    return out

_client = (None, None)


def get_client(client=None):
    global _client

    tmp_client = client is not None
    if not tmp_client:
        client = getattr(django_settings, 'SENTRY_CLIENT', 'raven.contrib.django.DjangoClient')

    if _client[0] != client:
        module, class_name = client.rsplit('.', 1)
        instance = getattr(__import__(module, {}, {}, class_name), class_name)(
            include_paths=set(getattr(django_settings, 'SENTRY_INCLUDE_PATHS', [])) | get_installed_apps(),
            exclude_paths=getattr(django_settings, 'SENTRY_EXCLUDE_PATHS', None),
            timeout=getattr(django_settings, 'SENTRY_TIMEOUT', None),
            servers=getattr(django_settings, 'SENTRY_SERVERS', None),
            name=getattr(django_settings, 'SENTRY_NAME', None),
            auto_log_stacks=getattr(django_settings, 'SENTRY_AUTO_LOG_STACKS', None),
            key=getattr(django_settings, 'SENTRY_KEY', md5_constructor(django_settings.SECRET_KEY).hexdigest()),
            string_max_length=getattr(django_settings, 'MAX_LENGTH_STRING', None),
            list_max_length=getattr(django_settings, 'MAX_LENGTH_LIST', None),
            site=getattr(django_settings, 'SENTRY_SITE', None),
            public_key=getattr(django_settings, 'SENTRY_PUBLIC_KEY', None),
            secret_key=getattr(django_settings, 'SENTRY_SECRET_KEY', None),
            project=getattr(django_settings, 'SENTRY_PROJECT', None),
            processors=getattr(django_settings, 'SENTRY_PROCESSORS', None),
            dsn=getattr(django_settings, 'SENTRY_DSN', None),
        )
        if not tmp_client:
            _client = (client, instance)
        return instance
    return _client[1]

client = get_client()


def get_transaction_wrapper(client):
    if client.servers:
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

    return transaction


def sentry_exception_handler(request=None, **kwargs):
    transaction = get_transaction_wrapper(get_client())

    @transaction.commit_on_success
    def actually_do_stuff(request=None, **kwargs):
        exc_info = sys.exc_info()
        try:
            if (django_settings.DEBUG and not getattr(django_settings, 'SENTRY_DEBUG', False)) or getattr(exc_info[0], 'skip_sentry', False):
                return

            if transaction.is_dirty():
                transaction.rollback()

            get_client().capture('Exception', exc_info=exc_info, request=request)
        except Exception, exc:
            try:
                logger.exception(u'Unable to process log entry: %s' % (exc,))
            except Exception, exc:
                warnings.warn(u'Unable to process log entry: %s' % (exc,))
        finally:
            try:
                del exc_info
            except Exception, e:
                logger.exception(e)

    return actually_do_stuff(request, **kwargs)

if 'raven.contrib.django' in django_settings.INSTALLED_APPS:
    got_request_exception.connect(sentry_exception_handler)
