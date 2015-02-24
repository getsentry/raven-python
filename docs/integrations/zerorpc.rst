ZeroRPC
=======

Setup
-----

The ZeroRPC integration comes as middleware for ZeroRPC. The middleware can be
configured like the original Raven client (using keyword arguments) and
registered into ZeroRPC's context manager::

    import zerorpc

    from raven.contrib.zerorpc import SentryMiddleware

    sentry = SentryMiddleware(dsn='udp://public_key:secret_key@example.com:4242/1')
    zerorpc.Context.get_instance().register_middleware(sentry)

By default, the middleware will hide internal frames from ZeroRPC when it
submits exceptions to Sentry. This behavior can be disabled by passing the
``hide_zerorpc_frames`` parameter to the middleware::

    sentry = SentryMiddleware(hide_zerorpc_frames=False, dsn='udp://public_key:secret_key@example.com:4242/1')

Compatibility
-------------

- ZeroRPC-Python < 0.4.0 is compatible with Raven <= 3.1.0;
- ZeroRPC-Python >= 0.4.0 requires Raven > 3.1.0.

Caveats
-------

Since sending an exception to Sentry will basically block your RPC call, you are
*strongly* advised to use the UDP server of Sentry. In any cases, a cleaner and
long term solution would be to make Raven requests to the Sentry server
asynchronous.
