Bottle
======

`Bottle <http://bottlepy.org/>`_ is a microframework for Python.  Raven
supports this framework through the WSGI integration.

Setup
-----

The first thing you'll need to do is to disable catchall in your Bottle app::

    import bottle

    app = bottle.app()
    app.catchall = False

.. note:: Bottle will not propagate exceptions to the underlying WSGI
          middleware by default. Setting catchall to False disables that.

Sentry will then act as Middleware::

    from raven import Client
    from raven.contrib.bottle import Sentry
    client = Client('___DSN___')
    app = Sentry(app, client)

Usage
-----

Once you've configured the Sentry application you need only call run with it::

    run(app=app)

If you want to send additional events, a couple of shortcuts are provided
on the Bottle request app object.

Capture an arbitrary exception by calling ``captureException``::

    try:
        1 / 0
    except ZeroDivisionError:
        request.app.sentry.captureException()

Log a generic message with ``captureMessage``::

    request.app.sentry.captureMessage('Hello, world!')
