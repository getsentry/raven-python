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


class ProxyClient(object):
    """
    A proxy which represents the currenty client at all times.
    """
    # introspection support:
    __members__ = property(lambda x: x.__dir__())

    # Need to pretend to be the wrapped class, for the sake of objects that care
    # about this (especially in equality tests)
    __class__ = property(lambda x: get_client().__class__)

    __dict__ = property(lambda o: get_client().__dict__)

    __repr__ = lambda: repr(get_client())
    __getattr__ = lambda x, o: getattr(get_client(), o)
    __setattr__ = lambda x, o, v: setattr(get_client(), o, v)
    __delattr__ = lambda x, o: delattr(get_client(), o)

    __lt__ = lambda x, o: get_client() < o
    __le__ = lambda x, o: get_client() <= o
    __eq__ = lambda x, o: get_client() == o
    __ne__ = lambda x, o: get_client() != o
    __gt__ = lambda x, o: get_client() > o
    __ge__ = lambda x, o: get_client() >= o
    __cmp__ = lambda x, o: cmp(get_client(), o)
    __hash__ = lambda x: hash(get_client())
    # attributes are currently not callable
    # __call__ = lambda x, *a, **kw: get_client()(*a, **kw)
    __nonzero__ = lambda x: bool(get_client())
    __len__ = lambda x: len(get_client())
    __getitem__ = lambda x, i: get_client()[i]
    __iter__ = lambda x: iter(get_client())
    __contains__ = lambda x, i: i in get_client()
    __getslice__ = lambda x, i, j: get_client()[i:j]
    __add__ = lambda x, o: get_client() + o
    __sub__ = lambda x, o: get_client() - o
    __mul__ = lambda x, o: get_client() * o
    __floordiv__ = lambda x, o: get_client() // o
    __mod__ = lambda x, o: get_client() % o
    __divmod__ = lambda x, o: get_client().__divmod__(o)
    __pow__ = lambda x, o: get_client() ** o
    __lshift__ = lambda x, o: get_client() << o
    __rshift__ = lambda x, o: get_client() >> o
    __and__ = lambda x, o: get_client() & o
    __xor__ = lambda x, o: get_client() ^ o
    __or__ = lambda x, o: get_client() | o
    __div__ = lambda x, o: get_client().__div__(o)
    __truediv__ = lambda x, o: get_client().__truediv__(o)
    __neg__ = lambda x: -(get_client())
    __pos__ = lambda x: +(get_client())
    __abs__ = lambda x: abs(get_client())
    __invert__ = lambda x: ~(get_client())
    __complex__ = lambda x: complex(get_client())
    __int__ = lambda x: int(get_client())
    __long__ = lambda x: long(get_client())
    __float__ = lambda x: float(get_client())
    __str__ = lambda x: str(get_client())
    __unicode__ = lambda x: unicode(get_client())
    __oct__ = lambda x: oct(get_client())
    __hex__ = lambda x: hex(get_client())
    __index__ = lambda x: get_client().__index__()
    __coerce__ = lambda x, o: x.__coerce__(x, o)
    __enter__ = lambda x: x.__enter__()
    __exit__ = lambda x, *a, **kw: x.__exit__(*a, **kw)

client = ProxyClient()


def get_client(client=None):
    global _client

    tmp_client = client is not None
    if not tmp_client:
        client = getattr(django_settings, 'SENTRY_CLIENT', 'raven.contrib.django.DjangoClient')

    if _client[0] != client:
        ga = lambda x, d=None: getattr(django_settings, 'SENTRY_%s' % x, d)

        module, class_name = client.rsplit('.', 1)

        options = getattr(django_settings, 'RAVEN_CONFIG', {})
        options.setdefault('servers', ga('SERVERS'))
        options.setdefault('include_paths', ga('INCLUDE_PATHS', []))
        options['include_paths'] = set(options['include_paths']) | get_installed_apps()
        options.setdefault('exclude_paths', ga('EXCLUDE_PATHS'))
        options.setdefault('timeout', ga('TIMEOUT'))
        options.setdefault('name', ga('NAME'))
        options.setdefault('auto_log_stacks', ga('AUTO_LOG_STACKS'))
        options.setdefault('key', ga('KEY', md5_constructor(django_settings.SECRET_KEY).hexdigest()))
        options.setdefault('string_max_length', ga('MAX_LENGTH_STRING'))
        options.setdefault('list_max_length', ga('MAX_LENGTH_LIST'))
        options.setdefault('site', ga('SITE'))
        options.setdefault('public_key', ga('PUBLIC_KEY'))
        options.setdefault('secret_key', ga('SECRET_KEY'))
        options.setdefault('project', ga('PROJECT'))
        options.setdefault('processors', ga('PROCESSORS'))
        options.setdefault('dsn', ga('DSN'))

        instance = getattr(__import__(module, {}, {}, class_name), class_name)(**options)
        if not tmp_client:
            _client = (client, instance)
        return instance
    return _client[1]


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
    transaction = get_transaction_wrapper(client)

    @transaction.commit_on_success
    def actually_do_stuff(request=None, **kwargs):
        exc_info = sys.exc_info()
        try:
            if not getattr(django_settings, 'RAVEN_CONFIG', {}).get('register_signals', not django_settings.DEBUG) or getattr(exc_info[1], 'skip_sentry', False):
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


def register_handlers():
    from django.core.signals import got_request_exception

    # Connect to Django's internal signal handler
    got_request_exception.connect(sentry_exception_handler)

    # If Celery is installed, register a signal handler
    if 'djcelery' in django_settings.INSTALLED_APPS:
        from raven.contrib.celery import register_signal

        try:
            register_signal(client)
        except Exception, e:
            logger.exception('Failed installing django-celery hook: %s' % e)


def register_serializers():
    import raven.contrib.django.serializers  # force import so serializers can call register

if 'raven.contrib.django' in django_settings.INSTALLED_APPS:
    # If we've explicitly enabled signals, or we're not running DEBUG, register handlers
    if getattr(django_settings, 'RAVEN_CONFIG', {}).get('register_signals', not django_settings.DEBUG):
        register_handlers()
    register_serializers()
