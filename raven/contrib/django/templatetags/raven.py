"""
raven.contrib.django.templatetags.raven
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2013 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

from django import template

register = template.Library()


@register.simple_tag
def sentry_public_dsn(scheme=None):
    from raven.contrib.django.models import client
    return client.get_public_dsn(scheme) or ''
    
@register.simple_tag
def sentry_tags(*tag_list):
    from raven.contrib.django.models import client
    tags = {}
    tag_list = tag_list or ['site', 'release']
    nounicode = lambda x : isinstance(x, unicode) and str(x) or x

    for tag in tag_list:
	    if hasattr(client, tag):
	    	tags[ nounicode(tag) ] = nounicode(getattr(client, tag))

    return tags
