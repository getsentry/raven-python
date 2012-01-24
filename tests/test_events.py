# -*- coding: utf-8 -*-

from mock import Mock
from unittest2 import TestCase
from raven.events import Message


class MessageTest(TestCase):
    def test_to_string(self):
        client = Mock()
        message = Message(client)

        data = {
            'sentry.interfaces.Message': {
                'message': 'My message from %s about %s',
            }
        }
        self.assertEqual(message.to_string(data),
                         'My message from UNDEFINED about UNDEFINED')

        data['sentry.interfaces.Message']['params'] = (1, 2)
        self.assertEqual(message.to_string(data),
                         'My message from 1 about 2')
