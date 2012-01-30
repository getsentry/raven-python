# -*- coding: utf-8 -*-

from unittest2 import TestCase
from celery.tests.utils import with_eager_tasks
from raven.base import Client
from raven.contrib.celery import make_celery_client


class TempStoreClient(Client):
    def __init__(self, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(servers=[], **kwargs)

    def send(self, **kwargs):
        self.events.append(kwargs)


class ClientTest(TestCase):
    def setUp(self):
        self.client = make_celery_client(TempStoreClient())

    def test_without_eager(self):
        self.client.create_from_text('test')

        # it should only have been queued
        self.assertEquals(len(self.client.events), 0)

    @with_eager_tasks
    def test_with_eager(self):
        self.client.create_from_text('test')

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'test')
