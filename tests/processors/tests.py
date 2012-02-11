# -*- coding: utf-8 -*-

from mock import Mock
from unittest2 import TestCase
from raven.processors import SanitizePasswordsProcessor


class SantizePasswordsProcessorTest(TestCase):
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

        self.assertTrue('sentry.interfaces.Stacktrace' in result)
        stack = result['sentry.interfaces.Stacktrace']
        self.assertTrue('frames' in stack)
        self.assertEquals(len(stack['frames']), 1)
        frame = stack['frames'][0]
        self.assertTrue('vars' in frame)
        vars = frame['vars']
        self.assertTrue('foo' in vars)
        self.assertEquals(vars['foo'], 'bar')
        self.assertTrue('password' in vars)
        self.assertEquals(vars['password'], proc.MASK)
        self.assertTrue('the_secret' in vars)
        self.assertEquals(vars['the_secret'], proc.MASK)
        self.assertTrue('a_password_here' in vars)
        self.assertEquals(vars['a_password_here'], proc.MASK)

    def test_http(self):
        data = {
            'sentry.interfaces.Http': {
                'body': {
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

        self.assertTrue('sentry.interfaces.Http' in result)
        http = result['sentry.interfaces.Http']
        for n in ('body', 'env', 'headers', 'cookies'):
            self.assertTrue(n in http)
            vars = http[n]
            self.assertTrue('foo' in vars)
            self.assertEquals(vars['foo'], 'bar')
            self.assertTrue('password' in vars)
            self.assertEquals(vars['password'], proc.MASK)
            self.assertTrue('the_secret' in vars)
            self.assertEquals(vars['the_secret'], proc.MASK)
            self.assertTrue('a_password_here' in vars)
            self.assertEquals(vars['a_password_here'], proc.MASK)
