from raven.utils.wsgi import get_headers, get_host, get_environ


class TestGetHeaders(object):
    def test_tuple_as_key(self):
        result = dict(get_headers({
            ('a', 'tuple'): 'foo',
        }))
        assert result == {}

    def test_coerces_http_name(self):
        result = dict(get_headers({
            'HTTP_ACCEPT': 'text/plain',
        }))
        assert 'Accept' in result
        assert result['Accept'] == 'text/plain'

    def test_coerces_content_type(self):
        result = dict(get_headers({
            'CONTENT_TYPE': 'text/plain',
        }))
        assert 'Content-Type' in result
        assert result['Content-Type'] == 'text/plain'

    def test_coerces_content_length(self):
        result = dict(get_headers({
            'CONTENT_LENGTH': '134',
        }))
        assert 'Content-Length' in result
        assert result['Content-Length'] == '134'


class TestGetEnviron(object):
    def test_has_remote_addr(self):
        result = dict(get_environ({'REMOTE_ADDR': '127.0.0.1'}))
        assert 'REMOTE_ADDR' in result
        assert result['REMOTE_ADDR'] == '127.0.0.1'

    def test_has_server_name(self):
        result = dict(get_environ({'SERVER_NAME': '127.0.0.1'}))
        assert 'SERVER_NAME' in result
        assert result['SERVER_NAME'] == '127.0.0.1'

    def test_has_server_port(self):
        result = dict(get_environ({'SERVER_PORT': 80}))
        assert 'SERVER_PORT' in result
        assert result['SERVER_PORT'] == 80

    def test_hides_wsgi_input(self):
        result = list(get_environ({'wsgi.input': 'foo'}))
        assert 'wsgi.input' not in result


class TestGetHost(object):
    def test_http_x_forwarded_host(self):
        result = get_host({'HTTP_X_FORWARDED_HOST': 'example.com'})
        assert result == 'example.com'

    def test_http_host(self):
        result = get_host({'HTTP_HOST': 'example.com'})
        assert result == 'example.com'

    def test_http_strips_port(self):
        result = get_host({
            'wsgi.url_scheme': 'http',
            'SERVER_NAME': 'example.com',
            'SERVER_PORT': '80',
        })
        assert result == 'example.com'

    def test_https_strips_port(self):
        result = get_host({
            'wsgi.url_scheme': 'https',
            'SERVER_NAME': 'example.com',
            'SERVER_PORT': '443',
        })
        assert result == 'example.com'

    def test_http_nonstandard_port(self):
        result = get_host({
            'wsgi.url_scheme': 'http',
            'SERVER_NAME': 'example.com',
            'SERVER_PORT': '81',
        })
        assert result == 'example.com:81'
