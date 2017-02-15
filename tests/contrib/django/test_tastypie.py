from __future__ import absolute_import

from tastypie.test import ResourceTestCase

from raven.contrib.django.models import client


class TastypieTest(ResourceTestCase):
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
