from __future__ import absolute_import

import django

from django.core.management import call_command
from django.test import TestCase
from mock import patch

from raven.contrib.django.models import client

DJANGO_18 = django.VERSION >= (1, 8, 0)


class RavenCommandTest(TestCase):
    @patch('raven.contrib.django.management.commands.raven.send_test_message')
    def test_basic(self, mock_send_test_message):
        call_command('raven', 'test')

        mock_send_test_message.assert_called_once_with(
            client, {
                'tags': None,
                'data': None,
            }
        )
