"""
raven.contrib.django
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logging
import sys

from raven.base import Client

logger = logging.getLogger('sentry.errors.client.django')

class DjangoClient(Client):
    logger = logging.getLogger('sentry.errors.client')

    def __init__(self, servers=None, **kwargs):
        super(DjangoClient, self).__init__(servers=servers, **kwargs)

    def process(self, **kwargs):
        from django.http import HttpRequest

        request = kwargs.pop('request', None)
        is_http_request = isinstance(request, HttpRequest)
        if is_http_request:
            try:
                post_data = request.raw_post_data and request.raw_post_data or request.POST
            except Exception:
                # assume we had a partial read:
                post_data = '<unavailable>'

            if not kwargs.get('data'):
                data = kwargs['data'] = {}
            else:
                data = kwargs['data']

            if not data.get('__sentry__'):
                data['__sentry__'] = {}

            kwargs['data'].update(dict(
                META=request.META,
                POST=post_data,
                GET=request.GET,
                COOKIES=request.COOKIES,
            ))

            if hasattr(request, 'user'):
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

                data['__sentry__']['user'] = user_info

            if not kwargs.get('url'):
                kwargs['url'] = request.build_absolute_uri()

        result = super(DjangoClient, self).process(**kwargs)

        if is_http_request:
            # attach the sentry object to the request
            request.sentry = {
                'id': self.get_ident(result),
            }

        return result

    def send(self, **kwargs):
        """
        Sends the message to the server.

        If ``servers`` was passed into the constructor, this will serialize the data and pipe it to
        each server using ``send_remote()``. Otherwise, this will communicate with ``sentry.models.GroupedMessage``
        directly.
        """
        if self.servers:
            return super(DjangoClient, self).send(**kwargs)
        else:
            from sentry.models import GroupedMessage

            return GroupedMessage.objects.from_kwargs(**kwargs)

    def create_from_exception(self, exc_info=None, **kwargs):
        """
        Creates an error log from an exception.
        """
        from django.template import TemplateSyntaxError
        from django.template.loader import LoaderOrigin

        new_exc = bool(exc_info)
        if not exc_info or exc_info is True:
            exc_info = sys.exc_info()

        data = kwargs.pop('data', {}) or {}

        if '__sentry__' not in data:
            data['__sentry__'] = {}

        try:
            exc_type, exc_value, exc_traceback = exc_info

            # As of r16833 (Django) all exceptions may contain a ``django_template_source`` attribute (rather than the
            # legacy ``TemplateSyntaxError.source`` check) which describes template information.
            if hasattr(exc_value, 'django_template_source') or ((isinstance(exc_value, TemplateSyntaxError) and \
                isinstance(getattr(exc_value, 'source', None), (tuple, list)) and isinstance(exc_value.source[0], LoaderOrigin))):
                origin, (start, end) = getattr(exc_value, 'django_template_source', exc_value.source)
                data['__sentry__']['template'] = (origin.reload(), start, end, origin.name)
                kwargs['view'] = origin.loadname

            return super(DjangoClient, self).create_from_exception(exc_info, **kwargs)
        finally:
            if new_exc:
                try:
                    del exc_info
                except Exception, e:
                    self.logger.exception(e)

    def create_from_record(self, record, **kwargs):
        """
        Creates an error log for a ``logging`` module ``record`` instance.
        """
        if not kwargs.get('request'):
            kwargs['request'] = record.__dict__.get('request')

        return super(DjangoClient, self).create_from_record(record, **kwargs)
