"""
raven.contrib.django.events
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2014 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import sys

from django.template import TemplateSyntaxError
from django.template.loader import LoaderOrigin

from raven.events import register, Exception as BaseException
from raven.contrib.django.utils import get_data_from_template

__all__ = ('Exception',)


@register
class Exception(BaseException):
    def capture(self, exc_info=None, stack=None, **kwargs):
        data = super(Exception, self).capture(exc_info, stack, **kwargs)
        if not exc_info or exc_info is True:
            exc_info = sys.exc_info()

        exc_value = exc_info[1]
        # As of r16833 (Django) all exceptions may contain a ``django_template_source`` attribute (rather than the
        # legacy ``TemplateSyntaxError.source`` check) which describes template information.
        if (
            hasattr(exc_value, 'django_template_source') or (
                (isinstance(exc_value, TemplateSyntaxError) and
                 isinstance(getattr(exc_value, 'source', None), (tuple, list)) and
                 isinstance(exc_value.source[0], LoaderOrigin))
            )
        ):
            source = getattr(exc_value, 'django_template_source', getattr(exc_value, 'source', None))
            if source is None:
                self.logger.info('Unable to get template source from exception')
            data.update(get_data_from_template(source))
        return data
