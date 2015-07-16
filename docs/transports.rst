Transports
==========

A transport is the mechanism in which Raven sends the HTTP request to the
Sentry server. By default, Raven uses a threaded asynchronous transport,
but you can easily adjust this by modifying your ``SENTRY_DSN`` value.

Transport registration is done via the URL prefix, so for example, a
synchronous transport is as simple as prefixing your ``SENTRY_DSN`` with
the ``sync+`` value.

Options are passed to transports via the querystring.

All transports should support at least the following options:

``timeout = 1``
  The time to wait for a response from the server, in seconds.

``verify_ssl = 1``
  If the connection is HTTPS, validate the certificate and hostname.

``ca_certs = [raven]/data/cacert.pem``
  A certificate bundle to use when validating SSL connections.

For example, to increase the timeout and to disable SSL verification::

	SENTRY_DSN = '___DSN___?timeout=5&verify_ssl=0'


aiohttp
-------

Should only be used within a :pep:`3156` compatible event loops
(*asyncio* itself and others).

::

    SENTRY_DSN = 'aiohttp+___DSN___'

Eventlet
--------

Should only be used within an Eventlet IO loop.

::

    SENTRY_DSN = 'eventlet+___DSN___'


Gevent
------

Should only be used within a Gevent IO loop.

::

    SENTRY_DSN = 'gevent+___DSN___'


Requests
--------

Requires the ``requests`` library. Synchronous.

::

    SENTRY_DSN = 'requests+___DSN___'


Sync
----

A synchronous blocking transport.

::

    SENTRY_DSN = 'sync+___DSN___'


Threaded (Default)
------------------

Spawns an async worker for processing messages.

::

    SENTRY_DSN = 'threaded+___DSN___'


Tornado
-------

Should only be used within a Tornado IO loop.

::

    SENTRY_DSN = 'tornado+___DSN___'


Twisted
-------

Should only be used within a Twisted event loop.

::

    SENTRY_DSN = 'twisted+___DSN___'
