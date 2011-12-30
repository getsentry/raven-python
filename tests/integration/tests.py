"""
Unfortunately these tests have to extend the django TestCase to ensure the Sentry server handles rollback.

Also, we have to directly query against the Sentry server models, which is undesirable.
"""

from __future__ import absolute_import

import logging

from django.test import TestCase
from sentry.models import Group, Event
from raven.contrib.django import DjangoClient


class ServerTest(TestCase):
    def setUp(self):
        self.raven = DjangoClient(include_paths=['tests'])

    def test_text(self):
        event_id, checksum = self.raven.capture('Message', message='hello')

        self.assertEquals(Group.objects.count(), 1)
        self.assertEquals(Event.objects.count(), 1)

        message = Event.objects.get()
        self.assertEquals(message.event_id, event_id)
        self.assertEquals(message.checksum, checksum)
        self.assertEquals(message.message, 'hello')
        self.assertEquals(message.logger, 'root')
        self.assertEquals(message.level, logging.ERROR)
        data = message.data
        self.assertTrue('modules' in data)
        versions = data['modules']
        self.assertTrue('tests' in versions)
        self.assertEquals(versions['tests'], '1.0')
        self.assertTrue('sentry.interfaces.Message' in data)
        message = data['sentry.interfaces.Message']
        self.assertEquals(message['message'], 'hello')
        self.assertEquals(message['params'], ())

    def test_exception(self):
        try:
            raise ValueError('hello')
        except:
            pass
        else:
            self.fail('Whatttt?')

        event_id, checksum = self.raven.capture('Exception')

        self.assertEquals(Group.objects.count(), 1)
        self.assertEquals(Event.objects.count(), 1)

        message = Event.objects.get()
        self.assertEquals(message.event_id, event_id)
        self.assertEquals(message.checksum, checksum)
        self.assertEquals(message.message, 'ValueError: hello')
        self.assertEquals(message.logger, 'root')
        self.assertEquals(message.level, logging.ERROR)
        data = message.data
        self.assertTrue('modules' in data)
        versions = data['modules']
        self.assertTrue('tests' in versions)
        self.assertEquals(versions['tests'], '1.0')
        self.assertTrue('sentry.interfaces.Exception' in data)
        exc = data['sentry.interfaces.Exception']
        self.assertEquals(exc['type'], 'ValueError')
        self.assertEquals(exc['value'], 'hello')
        self.assertTrue('sentry.interfaces.Stacktrace' in data)
        frames = data['sentry.interfaces.Stacktrace']['frames']
        frame = frames[0]
        self.assertEquals(frame['function'], 'test_exception')
        self.assertEquals(frame['module'], __name__)
        self.assertEquals(frame['filename'], 'tests/integration/tests.py')
        self.assertEquals(frame['abs_path'], __file__)
