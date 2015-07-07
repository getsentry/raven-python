Transports
==========

A transport is the mechanism in which Raven sends the HTTP request to the Sentry server. By default, Raven uses a threaded asynchronous transport, but you can easily adjust this by modifying your ``SENTRY_DSN`` value.

Transport registration is done as part of the Client configuration:

.. code-block:: python

  # Use the synchronous HTTP transport
  client = Client('http://public:secret@example.com/1', transport=HTTPTransport)

Options are passed to transports via the querystring.

All transports should support at least the following options:

``timeout = 1``
  The time to wait for a response from the server, in seconds.

``verify_ssl = 1``
  If the connection is HTTPS, validate the certificate and hostname.

``ca_certs = [raven]/data/cacert.pem``
  A certificate bundle to use when validating SSL connections.

For example, to increase the timeout and to disable SSL verification:

::

	SENTRY_DSN = 'http://public:secret@example.com/1?timeout=5&verify_ssl=0'


Builtin Transports
------------------

.. data:: sentry.transport.thread.ThreadedHTTPTransport

   The default transport. Manages a threaded worker for processing messages asynchronous.

.. data:: sentry.transport.http.HTTPTransport

   A synchronous blocking transport.

.. data:: sentry.transport.eventlet.EventletHTTPTransport

   Should only be used within an Eventlet IO loop.

.. data:: sentry.transport.gevent.GeventedHTTPTransport

   Should only be used within a Gevent IO loop.

.. data:: sentry.transport.requests.RequestsHTTPTransport

   A synchronous transport which relies on the ``requests`` library.

.. data:: sentry.transport.tornado.TornadoHTTPTransport

   Should only be used within a Tornado IO loop.

.. data:: sentry.transport.twisted.TwistedHTTPTransport

   Should only be used within a Twisted event loop.


Other Transports
----------------

- `aiohttp <https://github.com/getsentry/raven-aiohttp>`_
