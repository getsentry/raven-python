Configuring Tornado
===================

Setup
-----

The first thing you'll need to do is to initialize Raven under your
application

.. code-block:: python
   :emphasize-lines: 2,11,12,13

    import tornado.web
    from raven.contrib.tornado import AsyncSentryClient

    class MainHandler(tornado.web.RequestHandler):
        def get(self):
            self.write("Hello, world")

    application = tornado.web.Application([
        (r"/", MainHandler),
    ])
    application.sentry_client = AsyncSentryClient(
        'http://public_key:secret_key@host:port/project'
    )


Usage
-----

Once you've configured the Sentry application it will automatically
capture uncaught exceptions within Tornado.

Once the sentry client is attached to the application, request handlers
can send events using the shortcuts defined in the `SentryMixin` class.


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
            except Exception, e:
                response = yield tornado.gen.Task(
                    self.captureException, exc_info=True
                )
            self.finish()


.. tip::

   The value returned by the yield is a HTTPResponse obejct.


Synchronous
~~~~~~~~~~~

.. code-block:: python

    import tornado.web
    from raven.contrib.tornado import SentryMixin

    class AsyncExampleHandler(SentryMixin, tornado.web.RequestHandler):
        def get(self):
            self.write("You requested the main page")
            self.captureMessage("Request for main page served")

