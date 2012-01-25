# -*- coding: utf-8 -*-

from mock import Mock
from unittest2 import TestCase
from raven.events import Message


class MessageTest(TestCase):

    def test_to_string(self):
        unformatted_message = 'My message from %s about %s'
        client = Mock()
        message = Message(client)
        message.logger = Mock()
        data = {
            'sentry.interfaces.Message': {
                'message': unformatted_message,
            }
        }

        self.assertEqual(message.to_string(data), unformatted_message)

        data['sentry.interfaces.Message']['params'] = (1, 2)
        self.assertEqual(message.to_string(data),
                         unformatted_message % (1, 2))
