Configuring Flask
=================

Setup
-----

The first thing you'll need to do is to initialize Raven under your application::

    from raven.contrib.flask import Sentry
    sentry = Sentry(app, dsn='http://public_key:secret_key@example.com/1')

If you don't specify the ``dsn`` value, we will attempt to read it from your environment under
the ``SENTRY_DSN`` key.

Building applications on the fly? You can use Raven's ``init_app`` hook::

    sentry = Sentry(dsn='http://public_key:secret_key@example.com/1')

    def create_app():
        app = Flask(__name__)
        sentry.init_app(app)
        return app

Settings
--------

Additional settings for the client can be configured using ``SENTRY_<setting name>`` in your application's configuration::

    class MyConfig(object):
        SENTRY_DSN = 'http://public_key:secret_key@example.com/1'
        SENTRY_INCLUDE_PATHS = ['myproject']

Usage
-----

Once you've configured the Sentry application it will automatically capture uncaught exceptions within Flask. If you
want to send additional events, a couple of shortcuts are provided on the Sentry Flask middleware object.

Capture an arbitrary exception by calling ``captureException``::

    >>> try:
    >>>     1 / 0
    >>> except ZeroDivisionError:
    >>>     sentry.captureException()

Log a generic message with ``captureMessage``::

    >>> sentry.captureMessage('hello, world!')