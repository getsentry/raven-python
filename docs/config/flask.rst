Configuring Flask
=================

Setup
-----

The first thing you'll need to do is to initialize Raven under your application::

    from raven.contrib.flask import Sentry
    sentry = Sentry(app, dsn='http://public_key:secret_key@example.com/1')

.. note:: You may alternatively rely on Raven's ``init_app`` hook as well.

Settings
--------

Additional settings for the client can be configured using ``SENTRY_<setting name>`` in your application's configuration::

    class MyConfig(object):
        SENTRY_DSN = 'http://public_key:secret_key@example.com/1'
        SENTRY_INCLUDE_PATHS = ['myproject']
