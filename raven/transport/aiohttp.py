"""
raven.transport.aiohttp
~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2017 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
import asyncio

from raven.exceptions import APIError, RateLimited
from raven.transport.http import HTTPTransport

try:
    import aiohttp
    from aiohttp import ClientError
    has_aiohttp = True
except ImportError:
    has_aiohttp = False


class AIOHTTPHTTPTransport(HTTPTransport):

    scheme = ['aiohttp+http', 'aiohttp+https']

    def __init__(self, *args, **kwargs):
        if not has_aiohttp:
            raise ImportError('AIOHTTPHTTPTransport requires aiohttp.')
        loop = asyncio.get_event_loop()
        self.client = aiohttp.ClientSession(loop=loop)
        super().__init__(*args, **kwargs)

    async def send(self, url, data, headers):
        try:
            with aiohttp.Timeout(self.timeout):
                async with self.client.post(
                        url, data=data, headers=headers) as response:
                    try:
                        response.raise_for_status()
                    except ClientError as e:
                        msg = response.headers.get('x-sentry-error')
                        if response.status == 429:
                            try:
                                retry_after = int(response.headers.get('retry-after'))
                            except (ValueError, TypeError):
                                retry_after = 0
                            raise RateLimited(msg, retry_after)
                        raise APIError(msg, response.status) from e
                    else:
                        return response
        except asyncio.TimeoutError as e:
            message = ("Connection to Sentry server timed out "
                       "(url: %s, timeout: %d seconds)" % (url, self.timeout))
            raise APIError(message, 504) from e

    @staticmethod
    def handler(success, error, future):
        try:
            future.result()
            success()
        except Exception as e:
            error(e)
