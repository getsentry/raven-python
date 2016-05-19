# -*- coding: utf-8 -*-
"""
raven.contrib.django.client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import time
import logging

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.http import HttpRequest
from django.template import TemplateSyntaxError

try:
    # support Django 1.9
    from django.template.base import Origin
except ImportError:
    # backward compatibility
    from django.template.loader import LoaderOrigin as Origin

from raven.base import Client
from raven.contrib.django.utils import get_data_from_template, get_host
from raven.contrib.django.middleware import SentryLogMiddleware
from raven.utils.wsgi import get_headers, get_environ
from raven.utils import once
from raven import breadcrumbs
from raven._compat import string_types, binary_type

__all__ = ('DjangoClient',)


class _FormatConverter(object):

    def __init__(self, param_mapping):
        self.param_mapping = param_mapping
        self.params = []

    def __getitem__(self, val):
        self.params.append(self.param_mapping.get(val))
        return '%s'


def format_sql(sql, params):
    rv = []

    if isinstance(params, dict):
        conv = _FormatConverter(params)
        sql = sql % conv
        params = conv.params

    for param in params or ():
        if param is None:
            rv.append('NULL')
        elif isinstance(param, string_types):
            if isinstance(param, binary_type):
                param = param.decode('utf-8', 'replace')
            if len(param) > 256:
                param = param[:256] + u'…'
            rv.append("'%s'" % param.replace("'", "''"))
        else:
            rv.append(repr(param))

    return sql, rv


@once
def install_sql_hook():
    """If installed this causes Django's queries to be captured."""
    try:
        from django.db.backends.utils import CursorWrapper
    except ImportError:
        from django.db.backends.util import CursorWrapper

    try:
        real_execute = CursorWrapper.execute
        real_executemany = CursorWrapper.executemany
    except AttributeError:
        # XXX(mitsuhiko): On some very old django versions (<1.6) this
        # trickery would have to look different but I can't be bothered.
        return

    def record_sql(vendor, alias, start, duration, sql, params):
        def processor(data):
            real_sql, real_params = format_sql(sql, params)
            if real_params:
                real_sql = real_sql % tuple(real_params)
            # maybe category to 'django.%s.%s' % (vendor, alias or
            #   'default') ?
            data.update({
                'message': real_sql,
                'duration': duration,
                'category': 'query',
            })
        breadcrumbs.record(processor=processor)

    def record_many_sql(vendor, alias, start, sql, param_list):
        duration = time.time() - start
        for params in param_list:
            record_sql(vendor, alias, start, duration, sql, params)

    def execute(self, sql, params=None):
        start = time.time()
        try:
            return real_execute(self, sql, params)
        finally:
            record_sql(self.db.vendor, getattr(self.db, 'alias', None),
                       start, time.time() - start, sql, params)

    def executemany(self, sql, param_list):
        start = time.time()
        try:
            return real_executemany(self, sql, param_list)
        finally:
            record_many_sql(self.db.vendor, getattr(self.db, 'alias', None),
                            start, sql, param_list)

    CursorWrapper.execute = execute
    CursorWrapper.executemany = executemany
    breadcrumbs.ignore_logger('django.db.backends')


class DjangoClient(Client):
    logger = logging.getLogger('sentry.errors.client.django')

    def __init__(self, *args, **kwargs):
        install_sql_hook = kwargs.pop('install_sql_hook', True)
        Client.__init__(self, *args, **kwargs)
        if install_sql_hook:
            self.install_sql_hook()

    def install_sql_hook(self):
        install_sql_hook()

    def get_user_info(self, user):
        if hasattr(user, 'is_authenticated') and \
           not user.is_authenticated():
            return None

        user_info = {
            'id': user.pk,
        }

        if hasattr(user, 'email'):
            user_info['email'] = user.email

        if hasattr(user, 'get_username'):
            user_info['username'] = user.get_username()
        elif hasattr(user, 'username'):
            user_info['username'] = user.username

        return user_info

    def get_data_from_request(self, request):
        result = {}

        user = getattr(request, 'user', None)
        if user is not None:
            user_info = self.get_user_info(user)
            if user_info:
                result['user'] = user_info

        try:
            uri = request.build_absolute_uri()
        except SuspiciousOperation:
            # attempt to build a URL for reporting as Django won't allow us to
            # use get_host()
            if request.is_secure():
                scheme = 'https'
            else:
                scheme = 'http'
            host = get_host(request)
            uri = '%s://%s%s' % (scheme, host, request.path)

        if request.method not in ('GET', 'HEAD'):
            try:
                data = request.body
            except Exception:
                try:
                    data = request.raw_post_data
                except Exception:
                    # assume we had a partial read.
                    try:
                        data = request.POST or '<unavailable>'
                    except Exception:
                        data = '<unavailable>'
        else:
            data = None

        environ = request.META

        result.update({
            'request': {
                'method': request.method,
                'url': uri,
                'query_string': request.META.get('QUERY_STRING'),
                'data': data,
                'cookies': dict(request.COOKIES),
                'headers': dict(get_headers(environ)),
                'env': dict(get_environ(environ)),
            }
        })

        return result

    def build_msg(self, *args, **kwargs):
        data = super(DjangoClient, self).build_msg(*args, **kwargs)

        for frame in self._iter_frames(data):
            module = frame.get('module')
            if not module:
                continue

            if module.startswith('django.'):
                frame['in_app'] = False

        if not self.site and 'django.contrib.sites' in settings.INSTALLED_APPS:
            try:
                from django.contrib.sites.models import Site
                site = Site.objects.get_current()
                site_name = site.name or site.domain
                data['tags'].setdefault('site', site_name)
            except Exception:
                # Database error? Fallback to the id
                try:
                    data['tags'].setdefault('site', settings.SITE_ID)
                except AttributeError:
                    # SITE_ID wasn't set, so just ignore
                    pass

        return data

    def capture(self, event_type, request=None, **kwargs):
        if 'data' not in kwargs:
            kwargs['data'] = data = {}
        else:
            data = kwargs['data']

        if request is None:
            request = getattr(SentryLogMiddleware.thread, 'request', None)

        is_http_request = isinstance(request, HttpRequest)
        if is_http_request:
            data.update(self.get_data_from_request(request))

        if kwargs.get('exc_info'):
            exc_value = kwargs['exc_info'][1]
            # As of r16833 (Django) all exceptions may contain a
            # ``django_template_source`` attribute (rather than the legacy
            # ``TemplateSyntaxError.source`` check) which describes
            # template information.  As of Django 1.9 or so the new
            # template debug thing showed up.
            if hasattr(exc_value, 'django_template_source') or \
               ((isinstance(exc_value, TemplateSyntaxError) and
                isinstance(getattr(exc_value, 'source', None),
                           (tuple, list)) and
                isinstance(exc_value.source[0], Origin))) or \
               hasattr(exc_value, 'template_debug'):
                source = getattr(exc_value, 'django_template_source',
                                 getattr(exc_value, 'source', None))
                debug = getattr(exc_value, 'template_debug', None)
                if source is None:
                    self.logger.info('Unable to get template source from exception')
                data.update(get_data_from_template(source, debug))

        result = super(DjangoClient, self).capture(event_type, **kwargs)

        if is_http_request and result:
            # attach the sentry object to the request
            request.sentry = {
                'project_id': data.get('project', self.remote.project),
                'id': self.get_ident(result),
            }

        return result
