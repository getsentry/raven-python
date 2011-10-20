# -*- coding: utf-8 -*-

import inspect
from unittest2 import TestCase
from raven.base import Client
from raven.utils.stacks import iter_stack_frames

class TempStoreClient(Client):
    def __init__(self, servers=None, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(servers=servers, **kwargs)

    def send(self, **kwargs):
        self.events.append(kwargs)

class ClientTest(TestCase):
    def setUp(self):
        self.client = TempStoreClient()

    def test_message(self):
        self.client.create_from_text('test')

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'test')
        data = event['data']['__sentry__']
        self.assertFalse('frames' in data)

    def test_stack_explicit_frames(self):
        frames = inspect.stack()

        self.client.create_from_text('test', stack=iter_stack_frames(frames))

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'test')
        data = event['data']['__sentry__']
        self.assertTrue('frames' in data)
        self.assertEquals(len(frames), len(data['frames']))
        for frame, frame_i in zip(frames, data['frames']):
            self.assertEquals(frame[0].f_code.co_filename, frame_i['filename'])
            self.assertEquals(frame[0].f_code.co_name, frame_i['function'])

    def test_stack_auto_frames(self):
        self.client.create_from_text('test', stack=True)

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'test')
        data = event['data']['__sentry__']
        self.assertTrue('frames' in data)
