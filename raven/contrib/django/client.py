"""
raven.contrib.django.client
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logging

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.http import HttpRequest

from raven.base import Client
from raven.contrib.django.utils import get_host
from raven.contrib.django.middleware import SentryLogMiddleware
from raven.utils.wsgi import get_headers, get_environ

try:
    from django.contrib.auth.models import AbstractBaseUser as BaseUser
except ImportError:
    from django.contrib.auth.models import User as BaseUser  # NOQA

__all__ = ('DjangoClient',)


class DjangoClient(Client):
    logger = logging.getLogger('sentry.errors.client.django')

    def __init__(self, *args, **kwargs):
        super(DjangoClient, self).__init__(*args, **kwargs)
        self._local.request_added = False

    def is_enabled(self):
        return bool(self.servers or 'sentry' in settings.INSTALLED_APPS)

    def get_user_info(self, user):
        if not user.is_authenticated():
            return {'is_authenticated': False}

        user_info = {
            'id': user.pk,
            'is_authenticated': True,
        }

        if hasattr(user, 'email'):
            user_info['email'] = user.email

        if hasattr(user, 'get_username'):
            user_info['username'] = user.get_username()
        elif hasattr(user, 'username'):
            user_info['username'] = user.username

        return user_info

    def add_request(self, request):
        if hasattr(request, 'user') and isinstance(request.user, BaseUser):
            self.user_context(self.get_user_info(request.user))
        return self.add_http(self.get_data_from_request(request))

    def get_data_from_request(self, request):
        result = {}

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

        if request.method != 'GET':
            try:
                data = request.body
            except Exception:
                try:
                    data = request.raw_post_data
                except Exception:
                    # assume we had a partial read.
                    try:
                        data = dict(request.POST) or '<unavailable>'
                    except Exception:
                        data = '<unavailable>'
        else:
            data = None

        environ = request.META

        result.update({
            'method': request.method,
            'url': uri,
            'query_string': request.META.get('QUERY_STRING'),
            'data': data,
            'cookies': dict(request.COOKIES),
            'headers': dict(get_headers(environ)),
            'env': dict(get_environ(environ)),
        })

        return result

    def build_msg(self, *args, **kwargs):
        data = super(DjangoClient, self).build_msg(*args, **kwargs)

        for action in data['events']:
            if action.get('type', 'message') == 'exception' and 'stacktrace' in action:
                stacktrace = action['stacktrace']
                for frame in stacktrace['frames']:
                    module = frame.get('module')
                    if not module:
                        continue

                    if module[:7] == 'django.':
                        frame['in_app'] = False

        if not self.site and 'django.contrib.sites' in settings.INSTALLED_APPS:
            try:
                from django.contrib.sites.models import Site
                site = Site.objects.get_current()
                site_name = site.name or site.domain
                data['tags'].setdefault('site', site_name)
            except Exception:
                # Database error? Fallback to the id
                data['tags'].setdefault('site', settings.SITE_ID)

        return data

    def pre_add_action(self, action, **kwargs):
        request = action.pop('request', None)
        if request is None:
            request = getattr(SentryLogMiddleware.thread, 'request', None)

        if isinstance(request, HttpRequest):
            self.add_request(request)

    def capture(self, request=None, **kwargs):
        if 'data' not in kwargs:
            kwargs['data'] = data = {}
        else:
            data = kwargs['data']

        if request is None:
            request = getattr(SentryLogMiddleware.thread, 'request', None)

        result = super(DjangoClient, self).capture(**kwargs)

        if isinstance(request, HttpRequest) and result:
            # attach the sentry object to the request
            request.sentry = {
                'project_id': data.get('project', self.project),
                'id': self.get_ident(result),
            }

        return result

    def send(self, **kwargs):
        """
        Serializes and signs ``data`` and passes the payload off to ``send_remote``

        If ``servers`` was passed into the constructor, this will serialize the data and pipe it to
        each server using ``send_remote()``. Otherwise, this will communicate with ``sentry.models.GroupedMessage``
        directly.
        """
        if self.servers:
            return super(DjangoClient, self).send(**kwargs)
        elif 'sentry' in settings.INSTALLED_APPS:
            try:
                return self.send_integrated(kwargs)
            except Exception as e:
                self.error_logger.error(
                    'Unable to record event: %s\nEvent was: %r', e,
                    kwargs['message'], exc_info=True)

    def send_integrated(self, kwargs):
        from sentry.models import Group
        return Group.objects.from_kwargs(**kwargs)

    def reset(self):
        self._local.request_added = False
        super(DjangoClient, self).reset()
