ZeroRPC
=======

ZeroRPC is a light-weight, reliable and language-agnostic library for
distributed communication between server-side processes.

Setup
-----

The ZeroRPC integration comes as middleware for ZeroRPC. The middleware can be
configured like the original Raven client (using keyword arguments) and
registered into ZeroRPC's context manager::

    import zerorpc

    from raven.contrib.zerorpc import SentryMiddleware

    sentry = SentryMiddleware(dsn='___DSN___')
    zerorpc.Context.get_instance().register_middleware(sentry)

By default, the middleware will hide internal frames from ZeroRPC when it
submits exceptions to Sentry. This behavior can be disabled by passing the
``hide_zerorpc_frames`` parameter to the middleware::

    sentry = SentryMiddleware(hide_zerorpc_frames=False, dsn='___DSN___')

Compatibility
-------------

- ZeroRPC-Python < 0.4.0 is compatible with Raven <= 3.1.0;
- ZeroRPC-Python >= 0.4.0 requires Raven > 3.1.0.
