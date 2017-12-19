import asyncio

import pytest

from raven.contrib.aiohttp.client import AIOHTTPClient


@pytest.fixture
def mock_transport(request):

    class MockTransport:
        def __init__(self, *args, **kwargs):
            self.called = False

        async def send(self, url, data, headers):
            self.called = True
            if 'with_error' in request.keywords:
                raise ValueError

    return MockTransport


@pytest.mark.asyncio
@pytest.mark.parametrize('with_error', [False, True], ids=['without_error', 'with_error'])
async def test_aiohttp_client(mock_transport, mocker, with_error):
    dsn = 'htttps://user:pass@host:1234/1'
    client = AIOHTTPClient(dsn=dsn,
                           transport=mock_transport)
    success = mocker.spy(client, '_successful_send')
    failure = mocker.spy(client, '_log_failed_submission')
    client.captureMessage('test')

    await asyncio.sleep(.1)
    assert client.remote.get_transport().called
    if with_error:
        failure.assert_called()
    else:
        success.assert_called()
