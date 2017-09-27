# -*- coding: utf-8 -*-
"""
raven.tests.transport.sqs.tests
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.

:author: Mike Grima <mikegrima>
"""
from __future__ import absolute_import
import boto3

from raven.transport.sqs import SQSTransport
from raven.utils.testutils import TestCase
from raven.base import Client

# Simplify comparing dicts with primitive values:
from raven.utils import json
import zlib

from moto import mock_sqs

import base64


class SQSTest(TestCase):
    def test_sqs_transport(self):
        mock_sqs().start()
        sqs = boto3.client("sqs", region_name="us-east-1")
        sqs.create_queue(QueueName="sentry-queue")

        c = Client(dsn="mock://some_username:some_password@localhost:8143/1"
                       "?sqs_region=us-east-1&sqs_account=123456789012&sqs_name=sentry-queue",
                   transport=SQSTransport)

        data = dict(a=42, b=55, c=list(range(50)))
        expected_message = zlib.decompress(c.encode(data))

        c.send(**data)

        transport = c._transport_cache["mock://some_username:some_password@localhost:8143/1"
                                       "?sqs_region=us-east-1&sqs_account=123456789012"
                                       "&sqs_name=sentry-queue"].get_transport()

        self.assertEqual(transport.sqs_account, "123456789012")
        self.assertEqual(transport.sqs_name, "sentry-queue")
        self.assertTrue(type(transport.sqs_client).__name__, type(sqs).__name__)
        self.assertEquals(transport.queue_url, "https://queue.amazonaws.com/123456789012/sentry-queue")

        # Check SQS for the message that was sent over:
        messages = sqs.receive_message(QueueUrl=transport.queue_url)["Messages"]
        self.assertEqual(len(messages), 1)

        body = json.loads(messages[0]["Body"])

        self.assertEqual(body["url"], "mock://localhost:8143/api/1/store/")
        self.assertTrue("sentry_secret=some_password" in body["headers"]["X-Sentry-Auth"])

        decoded_data = base64.b64decode(body["data"])

        self.assertEqual(
            json.dumps(json.loads(expected_message.decode('utf-8')), sort_keys=True),
            json.dumps(c.decode(decoded_data), sort_keys=True)
        )

        mock_sqs().stop()
