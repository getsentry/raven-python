Configuring Flask
=================

Installation
------------

If you haven't already, install raven with its explicit Flask dependencies:

    pip install raven[flask]

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

If `Flask-Login <https://pypi.python.org/pypi/Flask-Login/>`_ is used by your application (including `Flask-Security <https://pypi.python.org/pypi/Flask-Security/>`_), user information will be captured when an exception or message is captured.
By default, only the ``id`` (current_user.get_id()), ``is_authenticated``, and ``is_anonymous`` is captured for the user.  If you would like additional attributes on the ``current_user`` to be captured,  you can configure them using ``SENTRY_USER_ATTRS``::

    class MyConfig(object):
        SENTRY_USER_ATTRS = ['username', 'first_name', 'last_name', 'email']

``email`` will be captured as ``sentry.interfaces.User.email``, and any additionl attributes will be available under ``sentry.interfaces.User.data``

You can specify the types of exceptions that should not be reported by Sentry client in your application by setting the ``RAVEN_IGNORE_EXCEPTIONS`` configuration value on your Flask app configuration::

    class MyExceptionType(Exception):
        def __init__(self, message):
            super(MyExceptionType, self).__init__(message)

    app = Flask(__name__)
    app.config["RAVEN_IGNORE_EXCEPTIONS"] = [MyExceptionType]

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