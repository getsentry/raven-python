# -*- coding: utf-8 -*-

from mock import Mock
from raven.utils.testutils import TestCase
from raven.processors import SanitizePasswordsProcessor, \
    RemovePostDataProcessor, RemoveStackLocalsProcessor


VARS = {
    'foo': 'bar',
    'password': 'hello',
    'the_secret': 'hello',
    'a_password_here': 'hello',
    'api_key': 'secret_key',
    'apiKey': 'secret_key',
}


class SantizePasswordsProcessorTest(TestCase):

    def _check_vars_sanitized(self, vars, proc):
        """
        Helper to check that keys have been sanitized.
        """
        self.assertTrue('foo' in vars)
        self.assertEquals(vars['foo'], 'bar')
        self.assertTrue('password' in vars)
        self.assertEquals(vars['password'], proc.MASK)
        self.assertTrue('the_secret' in vars)
        self.assertEquals(vars['the_secret'], proc.MASK)
        self.assertTrue('a_password_here' in vars)
        self.assertEquals(vars['a_password_here'], proc.MASK)
        self.assertTrue('api_key' in vars)
        self.assertEquals(vars['api_key'], proc.MASK)
        self.assertTrue('apiKey' in vars)
        self.assertEquals(vars['apiKey'], proc.MASK)

    def test_stacktrace(self):
        data = {
            'stacktrace': {
                'frames': [{'vars': VARS}],
            }
        }

        proc = SanitizePasswordsProcessor(Mock())
        result = proc.process(data)

        self.assertTrue('stacktrace' in result)
        stack = result['stacktrace']
        self.assertTrue('frames' in stack)
        self.assertEquals(len(stack['frames']), 1)
        frame = stack['frames'][0]
        self.assertTrue('vars' in frame)
        self._check_vars_sanitized(frame['vars'], proc)

    def test_http(self):
        data = {
            'request': {
                'data': VARS,
                'env': VARS,
                'headers': VARS,
                'cookies': VARS,
            }
        }

        proc = SanitizePasswordsProcessor(Mock())
        result = proc.process(data)

        self.assertTrue('request' in result)
        http = result['request']
        for n in ('data', 'env', 'headers', 'cookies'):
            self.assertTrue(n in http)
            self._check_vars_sanitized(http[n], proc)

    def test_querystring_as_string(self):
        data = {
            'request': {
                'query_string': 'foo=bar&password=hello&the_secret=hello'
                                '&a_password_here=hello&api_key=secret_key',
            }
        }

        proc = SanitizePasswordsProcessor(Mock())
        result = proc.process(data)

        self.assertTrue('request' in result)
        http = result['request']
        self.assertEquals(
            http['query_string'],
            'foo=bar&password=%(m)s&the_secret=%(m)s'
            '&a_password_here=%(m)s&api_key=%(m)s' % dict(m=proc.MASK))

    def test_querystring_as_string_with_partials(self):
        data = {
            'request': {
                'query_string': 'foo=bar&password&baz=bar',
            }
        }

        proc = SanitizePasswordsProcessor(Mock())
        result = proc.process(data)

        self.assertTrue('request' in result)
        http = result['request']
        self.assertEquals(http['query_string'], 'foo=bar&password&baz=bar' % dict(m=proc.MASK))

    def test_sanitize_credit_card(self):
        proc = SanitizePasswordsProcessor(Mock())
        result = proc.sanitize('foo', '4242424242424242')
        self.assertEquals(result, proc.MASK)

    def test_sanitize_credit_card_amex(self):
        # AMEX numbers are 15 digits, not 16
        proc = SanitizePasswordsProcessor(Mock())
        result = proc.sanitize('foo', '424242424242424')
        self.assertEquals(result, proc.MASK)


class RemovePostDataProcessorTest(TestCase):
    def test_does_remove_data(self):
        data = {
            'request': {
                'data': 'foo',
            }
        }

        proc = RemovePostDataProcessor(Mock())
        result = proc.process(data)

        self.assertTrue('request' in result)
        http = result['request']
        self.assertFalse('data' in http)


class RemoveStackLocalsProcessorTest(TestCase):
    def test_does_remove_data(self):
        data = {
            'stacktrace': {
                'frames': [{'vars': VARS}],
            }
        }
        proc = RemoveStackLocalsProcessor(Mock())
        result = proc.process(data)

        assert 'stacktrace' in result
        stack = result['stacktrace']
        for frame in stack['frames']:
            self.assertFalse('vars' in frame)
