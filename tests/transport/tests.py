# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from raven.utils.testutils import TestCase
from raven.base import Client

# Some internal stuff to extend the transport layer
from raven.transport import Transport
from raven.transport.exceptions import DuplicateScheme

# Simplify comparing dicts with primitive values:
from raven.utils import json

import datetime
import calendar
import pytz
import zlib


class DummyScheme(Transport):

    scheme = ['mock']

    def __init__(self, parsed_url, timeout=5):
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
        except DuplicateScheme:
            pass

    def test_basic_config(self):
        c = Client(
            dsn="mock://some_username:some_password@localhost:8143/1?timeout=1",
            name="test_server"
        )
        assert c.remote.options == {
            'timeout': '1',
        }

    def test_custom_transport(self):
        c = Client(dsn="mock://some_username:some_password@localhost:8143/1")

        data = dict(a=42, b=55, c=list(range(50)))
        c.send(**data)

        mock_cls = c._transport_cache['mock://some_username:some_password@localhost:8143/1'].get_transport()

        expected_message = zlib.decompress(c.encode(data))
        actual_message = zlib.decompress(mock_cls._data)

        # These loads()/dumps() pairs order the dict keys before comparing the string.
        # See GH504
        self.assertEqual(
            json.dumps(json.loads(expected_message.decode('utf-8')), sort_keys=True),
            json.dumps(json.loads(actual_message.decode('utf-8')), sort_keys=True)
        )

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
            'tags': {},
            'time_spent': None,
            'timestamp': 1336089600,
            'message': 'foo',
        }

        # The event_id is always overridden
        del msg['event_id']

        self.assertDictContainsSubset(expected, msg)
