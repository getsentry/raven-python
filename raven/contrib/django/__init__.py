"""
raven.contrib.django
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logging

from django.http import HttpRequest
from django.template import TemplateSyntaxError
from django.template.loader import LoaderOrigin

from raven.base import Client
from raven.contrib.django.utils import get_data_from_request, get_data_from_template

logger = logging.getLogger('sentry.errors.client.django')

class DjangoClient(Client):
    logger = logging.getLogger('sentry.errors.client')

    def __init__(self, servers=None, **kwargs):
        super(DjangoClient, self).__init__(servers=servers, **kwargs)

    def capture(self, event_type, request=None, **kwargs):
        if 'data' not in kwargs:
            kwargs['data'] = data = {}
        else:
            data = kwargs['data']

        is_http_request = isinstance(request, HttpRequest)
        if is_http_request:
            data.update(get_data_from_request(request))

        if kwargs.get('exc_info'):
            exc_value = kwargs['exc_info'][1]
            # As of r16833 (Django) all exceptions may contain a ``django_template_source`` attribute (rather than the
            # legacy ``TemplateSyntaxError.source`` check) which describes template information.
            if hasattr(exc_value, 'django_template_source') or ((isinstance(exc_value, TemplateSyntaxError) and \
               isinstance(getattr(exc_value, 'source', None), (tuple, list)) and isinstance(exc_value.source[0], LoaderOrigin))):
                data.update(get_data_from_template(getattr(exc_value, 'django_template_source', exc_value.source)))

        result = super(DjangoClient, self).capture(event_type, **kwargs)

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

