Configuring Flask
=================

Setup
-----

The first thing you'll need to do is to initialize Raven under your application::

    from raven.contrib.flask import Sentry
    sentry = Sentry(app)

.. note:: You may alternatively rely on Raven's ``init_app`` hook as well.

Settings
--------

Additional settings for the client are configured using ``SENTRY_<setting name>`` in your application's configuration::

    class MyConfig(object):
        SENTRY_KEY = 'my secret key'
        SENTRY_SERVERS = ['http://sentry.local/api/store/']