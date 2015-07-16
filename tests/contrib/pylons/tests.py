from raven.utils.testutils import TestCase
from raven.contrib.pylons import Sentry


def example_app(environ, start_response):
    raise ValueError('hello world')


class MiddlewareTest(TestCase):
    def setUp(self):
        self.app = example_app

    def test_init(self):
        config = {
            'sentry.dsn': 'http://public:secret@example.com/1',
        }
        middleware = Sentry(self.app, config)
