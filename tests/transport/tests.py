# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from raven.utils.testutils import TestCase
from raven.base import Client

# Some internal stuff to extend the transport layer
from raven.transport import Transport

import datetime
import calendar
import pytz


class DummyScheme(Transport):

    scheme = ['mock']

    def __init__(self, parsed_url, timeout=5):
        self.check_scheme(parsed_url)
        self._parsed_url = parsed_url
        self.timeout = timeout

    def send(self, data, headers):
        """
        Sends a request to a remote webserver
        """
        self._data = data
        self._headers = headers


class TransportTest(TestCase):
    def setUp(self):
        try:
            Client.register_scheme('mock', DummyScheme)
        except:
            pass

    def test_basic_config(self):
        c = Client(
            dsn="mock://some_username:some_password@localhost:8143/1?timeout=1",
            name="test_server"
        )
        assert c.transport_options == {
            'timeout': '1',
        }

    def test_custom_transport(self):
        c = Client(dsn="mock://some_username:some_password@localhost:8143/1")

        data = dict(a=42, b=55, c=list(range(50)))
        c.send(**data)

        expected_message = c.encode(data)
        self.assertIn('mock://localhost:8143/api/1/store/', Client._registry._transports)
        mock_cls = Client._registry._transports['mock://localhost:8143/api/1/store/']
        assert mock_cls._data == expected_message

    def test_build_then_send(self):
        c = Client(
            dsn="mock://some_username:some_password@localhost:8143/1",
            name="test_server")

        mydate = datetime.datetime(2012, 5, 4, tzinfo=pytz.utc)
        d = calendar.timegm(mydate.timetuple())
        msg = c.build_msg('raven.events.Message', message='foo', date=d)
        expected = {
            'project': '1',
            'sentry.interfaces.Message': {'message': 'foo', 'params': ()},
            'server_name': 'test_server',
            'level': 40,
            'modules': {},
            'tags': {},
            'time_spent': None,
            'timestamp': 1336089600,
            'message': 'foo',
        }

        # The event_id is always overridden
        del msg['event_id']

        self.assertDictContainsSubset(expected, msg)
