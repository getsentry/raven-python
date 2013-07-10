# -*- coding: utf-8 -*-

from mock import Mock
from raven.utils.testutils import TestCase
from raven.processors import SanitizePasswordsProcessor, RemovePostDataProcessor, \
  RemoveStackLocalsProcessor


class TestSantizePasswordsProcessor(object):
    def test_stacktrace(self):
        data = {
            'sentry.interfaces.Stacktrace': {
                'frames': [
                    {
                        'vars': {
                            'foo': 'bar',
                            'password': 'hello',
                            'the_secret': 'hello',
                            'a_password_here': 'hello',
                        },
                    }
                ]
            }
        }

        proc = SanitizePasswordsProcessor(Mock())
        result = proc.process(data)

        assert 'sentry.interfaces.Stacktrace' in result
        stack = result['sentry.interfaces.Stacktrace']
        assert 'frames' in stack
        assert len(stack['frames']) == 1
        frame = stack['frames'][0]
        assert 'vars' in frame
        vars = frame['vars']
        assert 'foo' in vars
        assert vars['foo'] == 'bar'
        assert 'password' in vars
        assert vars['password'] == proc.MASK
        assert 'the_secret' in vars
        assert vars['the_secret'] == proc.MASK
        assert 'a_password_here' in vars
        assert vars['a_password_here'] == proc.MASK

    def test_http(self):
        data = {
            'sentry.interfaces.Http': {
                'data': {
                    'foo': 'bar',
                    'password': 'hello',
                    'the_secret': 'hello',
                    'a_password_here': 'hello',
                },
                'env': {
                    'foo': 'bar',
                    'password': 'hello',
                    'the_secret': 'hello',
                    'a_password_here': 'hello',
                },
                'headers': {
                    'foo': 'bar',
                    'password': 'hello',
                    'the_secret': 'hello',
                    'a_password_here': 'hello',
                },
                'cookies': {
                    'foo': 'bar',
                    'password': 'hello',
                    'the_secret': 'hello',
                    'a_password_here': 'hello',
                },
            }
        }

        proc = SanitizePasswordsProcessor(Mock())
        result = proc.process(data)

        assert 'sentry.interfaces.Http' in result
        http = result['sentry.interfaces.Http']
        for n in ('data', 'env', 'headers', 'cookies'):
            assert n in http
            vars = http[n]
            assert 'foo' in vars
            assert vars['foo'] == 'bar'
            assert 'password' in vars
            assert vars['password'] == proc.MASK
            assert 'the_secret' in vars
            assert vars['the_secret'] == proc.MASK
            assert 'a_password_here' in vars
            assert vars['a_password_here'] == proc.MASK

    def test_querystring_as_string(self):
        data = {
            'sentry.interfaces.Http': {
                'query_string': 'foo=bar&password=hello&the_secret=hello&a_password_here=hello',
            }
        }

        proc = SanitizePasswordsProcessor(Mock())
        result = proc.process(data)

        assert 'sentry.interfaces.Http' in result
        http = result['sentry.interfaces.Http']
        expected = 'foo=bar&password=%(m)s&the_secret=%(m)s&a_password_here=%(m)s' % dict(m=proc.MASK)
        assert http['query_string'] == expected

    def test_querystring_as_string_with_partials(self):
        data = {
            'sentry.interfaces.Http': {
                'query_string': 'foo=bar&password&baz=bar',
            }
        }

        proc = SanitizePasswordsProcessor(Mock())
        result = proc.process(data)

        assert 'sentry.interfaces.Http' in result
        http = result['sentry.interfaces.Http']
        expected = 'foo=bar&password&baz=bar' % dict(m=proc.MASK)
        assert http['query_string'] == expected

    def test_sanitize_credit_card(self):
        proc = SanitizePasswordsProcessor(Mock())
        result = proc.sanitize('foo', '4242424242424242')
        assert result == proc.MASK

    def test_sanitize_credit_card_amex(self):
        # AMEX numbers are 15 digits, not 16
        proc = SanitizePasswordsProcessor(Mock())
        result = proc.sanitize('foo', '424242424242424')
        assert result == proc.MASK


class TestRemovePostDataProcessor(object):
    def test_does_remove_data(self):
        data = {
            'sentry.interfaces.Http': {
                'data': 'foo',
            }
        }

        proc = RemovePostDataProcessor(Mock())
        result = proc.process(data)

        assert 'sentry.interfaces.Http' in result
        http = result['sentry.interfaces.Http']
        assert 'data' not in http


class TestRemoveStackLocalsProcessor(object):
    def test_does_remove_data(self):
        data = {
            'sentry.interfaces.Stacktrace': {
                'frames': [
                    {
                        'vars': {
                            'foo': 'bar',
                            'password': 'hello',
                            'the_secret': 'hello',
                            'a_password_here': 'hello',
                        },
                    }
                ]
            }
        }
        proc = RemoveStackLocalsProcessor(Mock())
        result = proc.process(data)

        assert 'sentry.interfaces.Stacktrace' in result
        stack = result['sentry.interfaces.Stacktrace']
        for frame in stack['frames']:
            assert 'vars' not in frame
