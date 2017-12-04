import pytest

import django

from raven.contrib.django.resolver import RouteResolver

try:
    from django.conf.urls import url, include
except ImportError:
    # for Django version less than 1.4
    from django.conf.urls.defaults import url, include


@pytest.fixture
def route_resolver():
    return RouteResolver()


@pytest.fixture
def urlconf():
    if django.VERSION < (1, 9):
        included_url_conf = (
            url(r'^foo/bar/(?P<param>[\w]+)', lambda x: ''),
        ), '', ''
    else:
        included_url_conf = ((
            url(r'^foo/bar/(?P<param>[\w]+)', lambda x: ''),
        ), '')

    if django.VERSION >= (2, 0):
        from django.urls import path, re_path

        example_url_conf = (
            re_path(r'^api/(?P<project_id>[\w_-]+)/store/$', lambda x: ''),
            re_path(r'^report/', lambda x: ''),
            re_path(r'^example/', include(included_url_conf)),
            path('api/v2/<int:project_id>/store/', lambda x: '')
        )
        return example_url_conf
