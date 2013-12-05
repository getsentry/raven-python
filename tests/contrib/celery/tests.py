# -*- coding: utf-8 -*-

import mock

from celery.app import app_or_default

from raven.utils.testutils import TestCase
from raven.contrib.celery import CeleryClient


class ClientTest(TestCase):
    def setUp(self):
        self.client = CeleryClient(servers=['http://example.com'])

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
        self.client.captureMessage(message='test')

        self.assertEquals(send_raw.delay.call_count, 1)

    @mock.patch('raven.base.Client.send_encoded')
    def test_with_eager(self, send_encoded):
        """
        Integration test to ensure it propagates all the way down
        and calls the parent client's send_encoded method.
        """
        celery_app = app_or_default()
        celery_app.conf.CELERY_ALWAYS_EAGER = True

        self.client.captureMessage(message='test')

        self.assertEquals(send_encoded.call_count, 1)

        celery_app.conf.CELERY_ALWAYS_EAGER = False
