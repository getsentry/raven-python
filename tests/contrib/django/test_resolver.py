from __future__ import absolute_import

from raven.contrib.django.resolver import RouteResolver


def test_no_match():
    resolver = RouteResolver()
    result = resolver.resolve('/foo/bar', 'raven.contrib.django.urls')
    assert result == '/foo/bar'


def test_simple_match():
    resolver = RouteResolver()
    result = resolver.resolve('/report/', 'raven.contrib.django.urls')
    assert result == '/report/'


def test_complex_match():
    resolver = RouteResolver()
    result = resolver.resolve('/api/1234/store/', 'raven.contrib.django.urls')
    assert result == '/api/{project_id}/store/'
