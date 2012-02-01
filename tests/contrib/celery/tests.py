# -*- coding: utf-8 -*-

import mock
from unittest2 import TestCase
from celery.tests.utils import with_eager_tasks
from raven.contrib.celery import CeleryClient


class ClientTest(TestCase):
    def setUp(self):
        self.client = CeleryClient()

    @mock.patch('raven.contrib.celery.CeleryClient.send_raw')
    def test_send_encoded(self, send_raw):
        self.client.send_encoded('foo')

        send_raw.delay.assert_called_once_with('foo')

    @mock.patch('raven.contrib.celery.CeleryClient.send_raw')
    def test_without_eager(self, send_raw):
        """
        Integration test to ensure it propagates all the way down
        and calls delay on the task.
        """
        self.client.capture('Message', message='test')

        self.assertEquals(send_raw.delay.call_count, 1)

    @with_eager_tasks
    @mock.patch('raven.base.Client.send_encoded')
    def test_with_eager(self, send_encoded):
        """
        Integration test to ensure it propagates all the way down
        and calls the parent client's send_encoded method.
        """
        self.client.capture('Message', message='test')

        self.assertEquals(send_encoded.call_count, 1)
