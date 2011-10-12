"""
Unfortunately these tests have to extend the django TestCase to ensure the Sentry server handles rollback.

Also, we have to directly query against the Sentry server models, which is undesirable.
"""

from __future__ import absolute_import

import logging

from django.test import TestCase
from sentry.models import GroupedMessage, Message
from raven.contrib.django import DjangoClient

class ServerTest(TestCase):
    def setUp(self):
        self.raven = DjangoClient(include_paths=['tests'])

    def test_text(self):
        message_id, checksum = self.raven.create_from_text('hello')

        self.assertEquals(GroupedMessage.objects.count(), 1)
        self.assertEquals(Message.objects.count(), 1)

        message = Message.objects.get()
        self.assertEquals(message.message_id, message_id)
        self.assertEquals(message.checksum, checksum)
        self.assertEquals(message.message, 'hello')
        self.assertEquals(message.logger, 'root')
        self.assertEquals(message.level, logging.ERROR)
        data = message.data
        self.assertTrue('__sentry__' in data)
        self.assertTrue('versions' in data['__sentry__'])
        self.assertTrue('tests' in data['__sentry__']['versions'])
        self.assertEquals(data['__sentry__']['versions']['tests'], '1.0')

    def test_exception(self):
        try: raise ValueError('hello')
        except: pass
        else: self.fail('Whatttt?')

        message_id, checksum = self.raven.create_from_exception()

        self.assertEquals(GroupedMessage.objects.count(), 1)
        self.assertEquals(Message.objects.count(), 1)

        message = Message.objects.get()
        self.assertEquals(message.message_id, message_id)
        self.assertEquals(message.checksum, checksum)
        self.assertEquals(message.class_name, 'ValueError')
        self.assertEquals(message.message, 'hello')
        self.assertEquals(message.logger, 'root')
        self.assertEquals(message.level, logging.ERROR)
        data = message.data
        self.assertTrue('__sentry__' in data)
        self.assertTrue('versions' in data['__sentry__'])
        self.assertTrue('tests' in data['__sentry__']['versions'])
        self.assertEquals(data['__sentry__']['versions']['tests'], '1.0')
        self.assertTrue('frames' in data['__sentry__'])
        self.assertEquals(len(data['__sentry__']['frames']), 1)
        frame = data['__sentry__']['frames'][0]
        self.assertEquals(frame['function'], 'test_exception')
        self.assertEquals(frame['module'], __name__)
        self.assertEquals(frame['filename'], __file__)
        self.assertTrue('exception' in data['__sentry__'])
        exception = data['__sentry__']['exception']
        self.assertTrue(len(exception), 1)
        self.assertEquals(exception[0], '__builtin__')
        self.assertEquals(exception[1], ('hello',))
