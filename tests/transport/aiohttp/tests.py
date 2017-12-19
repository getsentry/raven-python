import asyncio
from unittest.mock import MagicMock

import aiohttp.web
from aiohttp.client import _RequestContextManager
from aiohttp.client_reqrep import ClientResponse
import pytest
from yarl import URL

from raven.contrib.aiohttp.client import AIOHTTPClient
import raven.transport.aiohttp
from raven.transport.aiohttp import AIOHTTPHTTPTransport


class PosterMock(MagicMock):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class TimeoutPosterMock(PosterMock):
    async def __aenter__(self):
        await asyncio.sleep(1.1)
        return self


class AsyncMockContextManager(_RequestContextManager):

    async def __aexit__(self, *args, **kwargs):
        pass


@pytest.fixture
def mock_client_post(mocker, request):
    if 'with_timeout' in request.keywords:
        mock = TimeoutPosterMock()
    else:
        mock = PosterMock()

    return mocker.patch.object(
        raven.transport.aiohttp.aiohttp.ClientSession, 'post', mock)


@pytest.fixture
def mock_client_post_error(mocker):

    mock = PosterMock(side_effect=aiohttp.ClientError())
    return mocker.patch.object(
        raven.transport.aiohttp.aiohttp.ClientSession, 'post', mock)


@pytest.fixture
def mock_client_post_throttled(mocker):
    throttled_response = ClientResponse(
        'get', URL('htttps://host:1234/api/1/store/'))
    throttled_response.status = 429
    throttled_response.headers = {'retry-after': 1}

    async def coro(resp):
        return resp

    mock = mocker.Mock(
        return_value=AsyncMockContextManager(coro(throttled_response)))
    return mocker.patch.object(
        raven.transport.aiohttp.aiohttp.ClientSession, 'post', mock)


@pytest.mark.asyncio
@pytest.mark.parametrize('with_timeout', [True, False],
                         ids=['with_timeout', 'without_timeout'])
async def test_aiohttp_http_transport(mock_client_post, with_timeout, caplog):
    dsn = 'htttps://user:pass@host:1234/1?timeout={:d}'.format(with_timeout)
    client = AIOHTTPClient(
        dsn=dsn, transport=AIOHTTPHTTPTransport,
    )
    client.captureMessage(message='test')
    await asyncio.sleep(int(with_timeout) + .1)
    if with_timeout:
        assert 'Connection to Sentry server timed out' in caplog.text()
    assert mock_client_post.call_args_list[0][0][0] == 'htttps://host:1234/api/1/store/'


@pytest.mark.asyncio
async def test_aiohttp_http_transport_with_error(mock_client_post_error, caplog):
    dsn = 'htttps://user:pass@host:1234/1'
    client = AIOHTTPClient(
        dsn=dsn, transport=AIOHTTPHTTPTransport,
    )
    client.captureMessage(message='test')
    await asyncio.sleep(.1)
    assert mock_client_post_error.call_args_list[0][0][0] == 'htttps://host:1234/api/1/store/'
    assert 'Sentry responded with an error' in caplog.text()


@pytest.mark.asyncio
async def test_aiohttp_http_transport_throttled(mock_client_post_throttled, caplog):
    dsn = 'htttps://user:pass@host:1234/1'
    client = AIOHTTPClient(
        dsn=dsn, transport=AIOHTTPHTTPTransport,
    )
    client.captureMessage(message='test')
    await asyncio.sleep(.1)
    assert mock_client_post_throttled.call_count == 1
    assert 'Sentry responded with an API error: RateLimited(None)' in caplog.text()
