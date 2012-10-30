# -*- coding: utf-8 -*-
"""
    tests

    Test the tornado Async Client
"""
import unittest
from mock import patch
from tornado import web, gen, testing
from raven.contrib.tornado import SentryMixin, AsyncSentryClient


class AnErrorProneHandler(SentryMixin, web.RequestHandler):
    def get(self):
        try:
            raise Exception("Damn it!")
        except Exception, e:
            self.captureException(True)


class SendErrorTestHandler(SentryMixin, web.RequestHandler):
    def get(self):
        raise Exception("Oops")

class SendErrorAsyncHandler(SentryMixin, web.RequestHandler):
    @web.asynchronous
    @gen.engine
    def get(self):
        raise Exception("Oops")


class AsyncMessageHandler(SentryMixin, web.RequestHandler):
    @web.asynchronous
    @gen.engine
    def get(self):
        # Compute something crazy
        response = yield gen.Task(
            self.captureMessage, "Something totally crazy was just done"
        )
        self.set_header('X-Sentry-ID', 'The ID')
        self.finish()

    def get_current_user(self):
        return {
            'name': 'John Doe'
        }


class TornadoAsyncClientTestCase(testing.AsyncHTTPTestCase):
    def get_app(self):
        app = web.Application([
            web.url(r'/an-error', AnErrorProneHandler),
            web.url(r'/an-async-message', AsyncMessageHandler),
            web.url(r'/send-error', SendErrorTestHandler),
            web.url(r'/send-error-async', SendErrorAsyncHandler),
        ])
        app.sentry_client = AsyncSentryClient(
            'http://public_key:secret_key@host:9000/project'
        )
        return app

    @patch('raven.contrib.tornado.AsyncSentryClient.send')
    def test_error_handler(self, send):
        response = self.fetch('/an-error?qs=qs')
        self.assertEqual(response.code, 200)
        self.assertEqual(send.call_count, 1)
        args, kwargs = send.call_args

        self.assertEqual(kwargs['public_key'], 'public_key')
        self.assertTrue(('sentry.interfaces.User' in kwargs))
        self.assertTrue(('sentry.interfaces.Stacktrace' in kwargs))
        self.assertTrue(('sentry.interfaces.Http' in kwargs))
        self.assertTrue(('sentry.interfaces.Exception' in kwargs))

        http_data = kwargs['sentry.interfaces.Http']
        self.assertEqual(http_data['cookies'], None)
        self.assertEqual(http_data['url'], response.effective_url)
        self.assertEqual(http_data['query_string'], 'qs=qs')
        self.assertEqual(http_data['method'], 'GET')

        user_data = kwargs['sentry.interfaces.User']
        self.assertEqual(user_data['is_authenticated'], False)

    @patch(
        'raven.contrib.tornado.AsyncSentryClient.send',
        side_effect=lambda *args, **kwargs: kwargs['callback']("done"))
    def test_message_handler(self, send):
        response = self.fetch('/an-async-message?qs=qs')
        self.assertEqual(response.code, 200)
        self.assertEqual(send.call_count, 1)
        args, kwargs = send.call_args

        self.assertEqual(kwargs['public_key'], 'public_key')
        self.assertTrue(('sentry.interfaces.User' in kwargs))
        self.assertTrue(('sentry.interfaces.Http' in kwargs))
        self.assertTrue(('sentry.interfaces.Message' in kwargs))

        http_data = kwargs['sentry.interfaces.Http']
        self.assertEqual(http_data['cookies'], None)
        self.assertEqual(http_data['url'], response.effective_url)
        self.assertEqual(http_data['query_string'], 'qs=qs')
        self.assertEqual(http_data['method'], 'GET')

        user_data = kwargs['sentry.interfaces.User']
        self.assertEqual(user_data['is_authenticated'], True)

    @patch('raven.contrib.tornado.AsyncSentryClient.send')
    def test_send_error_handler(self, send):
        response = self.fetch('/send-error?qs=qs')
        self.assertEqual(response.code, 500)
        self.assertEqual(send.call_count, 1)
        args, kwargs = send.call_args

        self.assertEqual(kwargs['public_key'], 'public_key')
        self.assertTrue(('sentry.interfaces.User' in kwargs))
        self.assertTrue(('sentry.interfaces.Stacktrace' in kwargs))
        self.assertTrue(('sentry.interfaces.Http' in kwargs))
        self.assertTrue(('sentry.interfaces.Exception' in kwargs))

        http_data = kwargs['sentry.interfaces.Http']
        self.assertEqual(http_data['cookies'], None)
        self.assertEqual(http_data['url'], response.effective_url)
        self.assertEqual(http_data['query_string'], 'qs=qs')
        self.assertEqual(http_data['method'], 'GET')

        user_data = kwargs['sentry.interfaces.User']
        self.assertEqual(user_data['is_authenticated'], False)

    @patch('raven.contrib.tornado.AsyncSentryClient.send')
    def test_send_error_handler_async(self, send):
        response = self.fetch('/send-error-async?qs=qs')
        self.assertEqual(response.code, 500)
        self.assertEqual(send.call_count, 1)
        args, kwargs = send.call_args

        self.assertEqual(kwargs['public_key'], 'public_key')
        self.assertTrue(('sentry.interfaces.User' in kwargs))
        self.assertTrue(('sentry.interfaces.Stacktrace' in kwargs))
        self.assertTrue(('sentry.interfaces.Http' in kwargs))
        self.assertTrue(('sentry.interfaces.Exception' in kwargs))

        http_data = kwargs['sentry.interfaces.Http']
        self.assertEqual(http_data['cookies'], None)
        self.assertEqual(http_data['url'], response.effective_url)
        self.assertEqual(http_data['query_string'], 'qs=qs')
        self.assertEqual(http_data['method'], 'GET')

        user_data = kwargs['sentry.interfaces.User']
        self.assertEqual(user_data['is_authenticated'], False)


if __name__ == '__main__':
    unittest.main()
