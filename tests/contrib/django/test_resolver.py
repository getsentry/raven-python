from __future__ import absolute_import

import pytest
import django

try:
    from django.conf.urls import url, include
except ImportError:
    # for Django version less than 1.4
    from django.conf.urls.defaults import url, include  # NOQA

from raven.contrib.django.resolver import RouteResolver


if django.VERSION < (1, 9):
    included_url_conf = (
        url(r'^foo/bar/(?P<param>[\w]+)', lambda x: ''),
    ), '', ''
else:
    included_url_conf = ((
        url(r'^foo/bar/(?P<param>[\w]+)', lambda x: ''),
    ), '')

example_url_conf = (
    url(r'^api/(?P<project_id>[\w_-]+)/store/$', lambda x: ''),
    url(r'^report/', lambda x: ''),
    url(r'^example/', include(included_url_conf)),
)


def test_no_match():
    resolver = RouteResolver()
    result = resolver.resolve('/foo/bar', example_url_conf)
    assert result == '/foo/bar'


def test_simple_match():  # TODO: ash add matchedstring to make this test actually test something
    resolver = RouteResolver()
    result = resolver.resolve('/report/', example_url_conf)
    assert result == '/report/'


def test_complex_match():
    resolver = RouteResolver()
    result = resolver.resolve('/api/1234/store/', example_url_conf)
    assert result == '/api/{project_id}/store/'


def test_included_match():
    resolver = RouteResolver()
    result = resolver.resolve('/example/foo/bar/baz', example_url_conf)
    assert result == '/example/foo/bar/{param}'


@pytest.mark.skipif(django.VERSION < (2, 0), reason="Requires Django > 2.0")
def test_newstyle_django20_urlconf(urlconf, route_resolver):
    result = route_resolver.resolve('/api/v2/1234/store/', urlconf)
    assert result == '/api/v2/{project_id}/store/'