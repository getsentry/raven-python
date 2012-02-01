"""
raven.contrib.django
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logging

from django.conf import settings
from django.http import HttpRequest
from django.template import TemplateSyntaxError
from django.template.loader import LoaderOrigin

from raven.base import Client
from raven.contrib.django.utils import get_data_from_template
from raven.utils.wsgi import get_headers, get_environ


class DjangoClient(Client):
    logger = logging.getLogger('sentry.errors.client.django')

    def __init__(self, servers=None, **kwargs):
        super(DjangoClient, self).__init__(servers=servers, **kwargs)

    def get_user_info(self, request):
        if request.user.is_authenticated():
            user_info = {
                'is_authenticated': True,
                'id': request.user.pk,
                'username': request.user.username,
                'email': request.user.email,
            }
        else:
            user_info = {
                'is_authenticated': False,
            }
        return user_info

    def get_data_from_request(self, request):
        if request.method == 'POST':
            try:
                data = request.raw_post_data and request.raw_post_data or request.POST
            except Exception:
                # assume we had a partial read:
                data = '<unavailable>'
        else:
            data = dict(request.REQUEST.items())

        environ = request.META

        result = {
            'sentry.interfaces.Http': {
                'method': request.method,
                'url': request.build_absolute_uri(),
                'query_string': request.META.get('QUERY_STRING'),
                'data': data,
                'cookies': dict(request.COOKIES),
                'headers': dict(get_headers(environ)),
                'env': dict(get_environ(environ)),
            }
        }

        if hasattr(request, 'user'):
            result['sentry.interfaces.User'] = self.get_user_info(request)

        return result

    def capture(self, event_type, request=None, **kwargs):
        if 'data' not in kwargs:
            kwargs['data'] = data = {}
        else:
            data = kwargs['data']

        is_http_request = isinstance(request, HttpRequest)
        if is_http_request:
            data.update(self.get_data_from_request(request))

        if kwargs.get('exc_info'):
            exc_value = kwargs['exc_info'][1]
            # As of r16833 (Django) all exceptions may contain a ``django_template_source`` attribute (rather than the
            # legacy ``TemplateSyntaxError.source`` check) which describes template information.
            if hasattr(exc_value, 'django_template_source') or ((isinstance(exc_value, TemplateSyntaxError) and \
               isinstance(getattr(exc_value, 'source', None), (tuple, list)) and isinstance(exc_value.source[0], LoaderOrigin))):
                source = getattr(exc_value, 'django_template_source', getattr(exc_value, 'source', None))
                if source is None:
                    self.logger.info('Unable to get template source from exception')
                data.update(get_data_from_template(source))

        result = super(DjangoClient, self).capture(event_type, **kwargs)

        if is_http_request:
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
            from sentry.models import Group
            try:
                return Group.objects.from_kwargs(**kwargs)
            except Exception, e:
                self.error_logger.error('Unable to record event: %s', e)
        else:
            self.error_logger.error('No servers configured, and sentry not installed. Cannot send message')
            return None
