from __future__ import absolute_import

try:
    from django.conf.urls import url, include
except ImportError:
    # for Django version less than 1.4
    from django.conf.urls.defaults import url, include  # NOQA

from raven.contrib.django.resolver import RouteResolver

included_url_conf = (
    url(r'^foo/bar/(?P<param>[\w]+)', lambda x: ''),
), '', ''

example_url_conf = (
    url(r'^api/(?P<project_id>[\w_-]+)/store/$', lambda x: ''),
    url(r'^example/', include(included_url_conf)),
)


def test_no_match():
    resolver = RouteResolver()
    result = resolver.resolve('/foo/bar', example_url_conf)
    assert result == '/foo/bar'


def test_simple_match():
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
