Transports
==========

A transport is the mechanism in which Raven sends the HTTP request to the Sentry server. By default, Raven uses a threaded asynchronous transport, but you can easily adjust this by modifying your ``SENTRY_DSN`` value.

Transport registration is done via the URL prefix, so for example, a synchronous transport is as simple as prefixing your ``SENTRY_DSN`` with the ``sync+`` value.

Options are passed to transports via the querystring.

All transports should support at least the following options:

``timeout = 1``
  The time to wait for a response from the server, in seconds.

``verify_ssl = 1``
  If the connection is HTTPS, validate the certificate and hostname.

``ca_certs = [raven]/data/cacert.pem``
  A certificate bundle to use when validating SSL conections.

For example, to increase the timeout and to disable SSL verification:

::

	SENTRY_DSN = 'http://public:secret@example.com/1?timeout=5&verify_ssl=0'


Eventlet
--------

Should only be used within an Eventlet IO loop.

::

    SENTRY_DSN = 'eventlet+http://public:secret@example.com/1'


Gevent
------

Should only be used within a Gevent IO loop.

::

    SENTRY_DSN = 'gevent+http://public:secret@example.com/1'


Requests
--------

Requires the ``requests`` library. Synchronous.

::

    SENTRY_DSN = 'requests+http://public:secret@example.com/1'


Sync
----

A synchronous blocking transport.

::

    SENTRY_DSN = 'sync+http://public:secret@example.com/1'


Threaded (Default)
------------------

Spawns a async worked for processing messages.

::

    SENTRY_DSN = 'threaded+http://public:secret@example.com/1'


Tornado
-------

Should only be used within a Tornado IO loop.

::

    SENTRY_DSN = 'tornado+http://public:secret@example.com/1'


Twisted
-------

Should only be used within a Twisted event loop.

::

    SENTRY_DSN = 'twisted+http://public:secret@example.com/1'

