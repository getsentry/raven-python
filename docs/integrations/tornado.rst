Tornado
=======

Tornado is an async web framework for Python.

Setup
-----

The first thing you'll need to do is to initialize sentry client under
your application

.. code-block:: python

    import tornado.web
    from raven.contrib.tornado import AsyncSentryClient

    class MainHandler(tornado.web.RequestHandler):
        def get(self):
            self.write("Hello, world")

    application = tornado.web.Application([
        (r"/", MainHandler),
    ])
    application.sentry_client = AsyncSentryClient(
        '___DSN___'
    )


Usage
-----

Once the sentry client is attached to the application, request handlers
can automatically capture uncaught exceptions by inheriting the `SentryMixin` class.

.. code-block:: python

    import tornado.web
    from raven.contrib.tornado import SentryMixin

    class UncaughtExceptionExampleHandler(
            SentryMixin, tornado.web.RequestHandler):
        def get(self):
            1/0


You can also send events manually using the shortcuts defined in `SentryMixin`.
The shortcuts can be used for both asynchronous and synchronous usage.


Asynchronous
~~~~~~~~~~~~

.. code-block:: python

    import tornado.web
    import tornado.gen
    from raven.contrib.tornado import SentryMixin

    class AsyncMessageHandler(SentryMixin, tornado.web.RequestHandler):
        @tornado.web.asynchronous
        @tornado.gen.engine
        def get(self):
            self.write("You requested the main page")
            yield tornado.gen.Task(
                self.captureMessage, "Request for main page served"
            )
            self.finish()

    class AsyncExceptionHandler(SentryMixin, tornado.web.RequestHandler):
        @tornado.web.asynchronous
        @tornado.gen.engine
        def get(self):
            try:
                raise ValueError()
            except Exception as e:
                response = yield tornado.gen.Task(
                    self.captureException, exc_info=True
                )
            self.finish()


.. tip::

   The value returned by the yield is a ``HTTPResponse`` object.


Synchronous
~~~~~~~~~~~

.. code-block:: python

    import tornado.web
    from raven.contrib.tornado import SentryMixin

    class AsyncExampleHandler(SentryMixin, tornado.web.RequestHandler):
        def get(self):
            self.write("You requested the main page")
            self.captureMessage("Request for main page served")
