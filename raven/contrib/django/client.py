"""
raven.contrib.django.client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logging

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.http import HttpRequest
from django.template import TemplateSyntaxError
from django.template.loader import LoaderOrigin

from raven.base import Client
from raven.contrib.django.utils import get_data_from_template, get_host
from raven.contrib.django.middleware import SentryLogMiddleware
from raven.utils.wsgi import get_headers, get_environ

__all__ = ('DjangoClient',)


class DjangoClient(Client):
    logger = logging.getLogger('sentry.errors.client.django')

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

    def get_data_from_request(self, request):
        try:
            from django.contrib.auth.models import AbstractBaseUser as BaseUser
        except ImportError:
            from django.contrib.auth.models import User as BaseUser  # NOQA

        result = {}

        if hasattr(request, 'user') and isinstance(request.user, BaseUser):
            result['user'] = self.get_user_info(request.user)

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

        stacks = [
            data.get('stacktrace'),
        ]
        if 'exception' in data:
            stacks.append(data['exception']['values'][0]['stacktrace'])

        for stacktrace in filter(bool, stacks):
            for frame in stacktrace['frames']:
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
                data['tags'].setdefault('site', settings.SITE_ID)

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
            # As of r16833 (Django) all exceptions may contain a ``django_template_source`` attribute (rather than the
            # legacy ``TemplateSyntaxError.source`` check) which describes template information.
            if hasattr(exc_value, 'django_template_source') or ((isinstance(exc_value, TemplateSyntaxError) and
               isinstance(getattr(exc_value, 'source', None), (tuple, list)) and isinstance(exc_value.source[0], LoaderOrigin))):
                source = getattr(exc_value, 'django_template_source', getattr(exc_value, 'source', None))
                if source is None:
                    self.logger.info('Unable to get template source from exception')
                data.update(get_data_from_template(source))

        result = super(DjangoClient, self).capture(event_type, **kwargs)

        if is_http_request and result:
            # attach the sentry object to the request
            request.sentry = {
                'project_id': data.get('project', self.remote.project),
                'id': self.get_ident(result),
            }

        return result
