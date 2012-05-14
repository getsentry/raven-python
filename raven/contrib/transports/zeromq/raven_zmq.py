"""
This demonstrates how to implement your own transport for Raven.
"""

from raven.transport import Transport

import json


class MissingLibrary(StandardError):
    pass

try:
    import zmq
    ZMQ_CONTEXT = zmq.Context()
except:
    ZMQ_CONTEXT = None
    msg = "You need to have pyzmq installed"
    raise MissingLibrary(msg)


class ZmqPubTransport(Transport):
    """
    This provides a zeromq publisher transport.

    This transport does *not* do initial handshaking so it it
    susceptible to initially dropped messages due to the "slow joiner"
    problem.

    Note that the scheme here indicates a pub socket over tcp
    """
    scheme = ['zmq+tcp']

    def __init__(self, parsed_url):
        self.check_scheme(parsed_url)
        self._parsed_url = parsed_url

        self._zmq_url = parsed_url.geturl().replace("zmq+", '')

        self._sock = ZMQ_CONTEXT.socket(zmq.PUB)
        self._sock.setsockopt(zmq.LINGER, 0)
        self._sock.connect(self._zmq_url)

    def send(self, data, headers):
        """
        Just push a message out as JSON and include everything
        """
        self._sock.send(json.dumps({'data': data, 'headers':
            headers}))

    def compute_scope(self, url, scope):
        scope.update({
            'SENTRY_SERVERS': [url.geturl()],
            'SENTRY_PROJECT': '',
            'SENTRY_PUBLIC_KEY': 'fake_user',
            'SENTRY_SECRET_KEY': 'fake_password',
        })
        return scope
