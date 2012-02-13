from unittest2 import TestCase
from raven.utils.wsgi import get_headers, get_host, get_environ


class GetHeadersTest(TestCase):
    def test_tuple_as_key(self):
        result = dict(get_headers({
            ('a', 'tuple'): 'foo',
        }))
        self.assertEquals(result, {})

    def test_coerces_http_name(self):
        result = dict(get_headers({
            'HTTP_ACCEPT': 'text/plain',
        }))
        self.assertIn('Accept', result)
        self.assertEquals(result['Accept'], 'text/plain')

    def test_coerces_content_type(self):
        result = dict(get_headers({
            'CONTENT_TYPE': 'text/plain',
        }))
        self.assertIn('Content-Type', result)
        self.assertEquals(result['Content-Type'], 'text/plain')

    def test_coerces_content_length(self):
        result = dict(get_headers({
            'CONTENT_LENGTH': '134',
        }))
        self.assertIn('Content-Length', result)
        self.assertEquals(result['Content-Length'], '134')


class GetEnvironTest(TestCase):
    def test_has_remote_addr(self):
        result = dict(get_environ({'REMOTE_ADDR': '127.0.0.1'}))
        self.assertIn('REMOTE_ADDR', result)
        self.assertEquals(result['REMOTE_ADDR'], '127.0.0.1')

    def test_has_server_name(self):
        result = dict(get_environ({'SERVER_NAME': '127.0.0.1'}))
        self.assertIn('SERVER_NAME', result)
        self.assertEquals(result['SERVER_NAME'], '127.0.0.1')

    def test_has_server_port(self):
        result = dict(get_environ({'SERVER_PORT': 80}))
        self.assertIn('SERVER_PORT', result)
        self.assertEquals(result['SERVER_PORT'], 80)

    def test_hides_wsgi_input(self):
        result = list(get_environ({'wsgi.input': 'foo'}))
        self.assertNotIn('wsgi.input', result)


class GetHostTest(TestCase):
    def test_http_x_forwarded_host(self):
        result = get_host({'HTTP_X_FORWARDED_HOST': 'example.com'})
        self.assertEquals(result, 'example.com')

    def test_http_host(self):
        result = get_host({'HTTP_HOST': 'example.com'})
        self.assertEquals(result, 'example.com')

    def test_http_strips_port(self):
        result = get_host({
            'wsgi.url_scheme': 'http',
            'SERVER_NAME': 'example.com',
            'SERVER_PORT': '80',
        })
        self.assertEquals(result, 'example.com')

    def test_https_strips_port(self):
        result = get_host({
            'wsgi.url_scheme': 'https',
            'SERVER_NAME': 'example.com',
            'SERVER_PORT': '443',
        })
        self.assertEquals(result, 'example.com')

    def test_http_nonstandard_port(self):
        result = get_host({
            'wsgi.url_scheme': 'http',
            'SERVER_NAME': 'example.com',
            'SERVER_PORT': '81',
        })
        self.assertEquals(result, 'example.com:81')
