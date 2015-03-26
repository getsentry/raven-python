Tornado
=======

Setup
-----

The first thing you'll need to do is to initialize sentry client under
your application

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

Once the sentry client is attached to the application, request handlers
can automatically capture uncaught exceptions by inheriting the `SentryMixin` class.

.. code-block:: python

    import tornado.web
    from raven.contrib.tornado import SentryMixin

    class UncaughtExceptionExampleHandler(SentryMixin, tornado.web.RequestHandler):
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


Request Body Filtering
~~~~~~~~~~~

If you expect files or large body sizes, you may want to truncate or otherwise
filter the body.

.. code-block:: python

    import tornado.web
    from raven.contrib.tornado import SentryMixin

    class AsyncExampleHandler(SentryMixin, tornado.web.RequestHandler):
        # Strip files and ensure the body is small enough
        def get_sentry_request_body(self):
            if len(self.request.files)>0 or len(self.request.body) > 200000:
                files = {k:[{dk:dv for dk, dv in d.iteritems() if dk!='body'}for d in v] for k,v in self.request.files.iteritems()}
                data = { 'arguments': self.request.arguments, 'files': files } 
            else:
                data = self.request.body

            return data
