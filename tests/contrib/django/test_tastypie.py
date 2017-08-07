from __future__ import absolute_import

import django
import pytest

from django.test import TestCase
from django.core.urlresolvers import get_resolver
from tastypie.test import ResourceTestCaseMixin

from raven.contrib.django.models import client
from raven.contrib.django.resolver import RouteResolver

DJANGO_19 = django.VERSION >= (1, 9, 0) and django.VERSION <= (1, 10, 0)


class TastypieTest(ResourceTestCaseMixin, TestCase):
    def setUp(self):
        super(TastypieTest, self).setUp()
        self.path = '/api/v1/example/'

    def test_list_break(self):
        self.api_client.get(self.path)

        assert len(client.events) == 1
        event = client.events.pop(0)
        assert 'exception' in event
        exc = event['exception']['values'][-1]
        assert exc['type'] == 'Exception'
        assert exc['value'] == 'oops'
        assert 'request' in event
        assert event['request']['url'] == 'http://testserver/api/v1/example/'

    def test_create_break(self):
        self.api_client.post('/api/v1/example/')

        assert len(client.events) == 1
        event = client.events.pop(0)
        assert 'exception' in event
        exc = event['exception']['values'][-1]
        assert exc['type'] == 'Exception'
        assert exc['value'] == 'oops'
        assert 'request' in event
        assert event['request']['url'] == 'http://testserver/api/v1/example/'

    def test_update_break(self):
        self.api_client.put('/api/v1/example/foo/', data={'name': 'bar'})

        assert len(client.events) == 1
        event = client.events.pop(0)
        assert 'exception' in event
        exc = event['exception']['values'][-1]
        assert exc['type'] == 'Exception'
        assert exc['value'] == 'oops'
        assert 'request' in event
        assert event['request']['url'] == 'http://testserver/api/v1/example/foo/'

    @pytest.mark.skipif(not DJANGO_19, reason='Django != 1.9')
    def test_resolver(self):
        resolver = get_resolver()
        route_resolver = RouteResolver()
        result = route_resolver._resolve(resolver, '/api/v1/example/')
        assert result == '/api/{api_name}/{resource_name}/'
