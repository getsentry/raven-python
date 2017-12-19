import asyncio
from functools import partial

from raven.base import Client


def task_callback(client, failed_send, future):
    try:
        future.result()
    except Exception as e:
        if client.raise_send_errors:
            raise e
        failed_send(e)
    else:
        client._successful_send()


class AIOHTTPClient(Client):
    def send_remote(self, url, data, headers=None):
        # If the client is configured to raise errors on sending,
        # the implication is that the backoff and retry strategies
        # will be handled by the calling application
        if headers is None:
            headers = {}

        if not self.raise_send_errors and not self.state.should_try():
            data = self.decode(data)
            self._log_failed_submission(data)
            return

        self.logger.debug('Sending message of length %d to %s', len(data), url)

        def failed_send(e):
            self._failed_send(e, url, self.decode(data))

        transport = self.remote.get_transport()
        task = asyncio.ensure_future(transport.send(url, data, headers))
        task.add_done_callback(partial(task_callback, self, failed_send))
