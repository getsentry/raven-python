Logging Breadcrumbs
===================

Newer Sentry versions support logging of breadcrumbs in addition of
errors.  This means that whenever an error or other Sentry event is
submitted to the system, breadcrumbs that were logged before are sent
along to make it easier to reproduce what lead up to an error.

In the default configuration the Python client instruments the logging
framework and a few popular libraries to emit crumbs.

You can however also manually emit events if you want to do so.  There are
a few ways this can be done.

Breadcrumbs are enabled by default but starting with Raven 5.15 you can
disable them on a per-client basis by passing ``enable_breadcrumbs=False``
to the client constructor.

Enabling / Disabling Instrumentation
------------------------------------

When a sentry client is constructed then the raven library will by default
automatically instrument some popular libraries.  There are a few ways
this can be controlled by passing parameters to the client constructor:

``install_logging_hook``:
    If this keyword argument is set to `False` the Python logging system
    will not be instrumented.  Note that this is a global instrumentation
    so that if you are using multiple sentry clients at once you need to
    disable this on all of them.

``hook_libraries``:
    This is a list of libraries that you want to hook.  The default is to
    hook all libraries that we have integrations for.  If this is set to
    an empty list then no libraries are hooked.

    The following libraries are supported currently:

    -   ``'requests'``: hooks the Python requests library.
    -   ``'httplib'``: hooks the stdlib http library (also hooks urllib in
        the process)

Additionally framework integration will hook more things automatically.
For instance when you use Django, database queries will be recorded.

Another option to control what happens is to register special handlers for
the logging system or to disable loggers entirely.  For this you can use
the :py:func:`~raven.breadcrumbs.ignore_logger` and
:py:func:`~raven.breadcrumbs.register_special_log_handler` functions:

.. py:function:: raven.breadcrumbs.ignore_logger(name_or_logger)

    If called with the name of a logger, this will ignore all messages
    that come from that logger.  For instance if you have a very spammy
    logger you can disable it this way.

.. py:function:: raven.breadcrumbs.register_special_log_handler(name_or_logger, callback)

    This registers a callback as a handler for a given logger.  This can
    be used to ignore or convert log messages.  The callback is invoked
    with the following arguments: ``logger, level, msg, args, kwargs``.
    If the callback returns `False` nothing is logged, if it returns
    `True` the default handling kicks in.

    Typically it makes sense to invoke
    :py:func:`~raven.breadcrumbs.record` from it.

.. py:function:: raven.breadcrumbs.register_logging_handler(callback)

    This is similar to :py:func:`~raven.breadcrumbs.register_special_log_handler`
    but it adds a global callback that is invoked for all log entries.
    Otherwise it works the same but multiple handlers can be registered.

Manually Emitting Breadcrumbs
-----------------------------

If you want to manually record breadcrumbs the most convenient way to do
that is to use the :py:func:`~reaven.breadcrumbs.record` function
which will automatically record the crumbs with the clients that are
working with the current thread.  This is more convenient than to call the
`captureBreadcrumb` method on the client itself as you need to hold a
reference to that.

.. py:function:: raven.breadcrumbs.record(**options)

    This function accepts keyword arguments matching the attributes of a
    breadcrumb.  For more information see :doc:`/clientdev/interfaces`.
    Additionally a `processor` callback can be passed which will be
    invoked to process the data if the crumb was not rejected.

    The most important parameters:

    `message`:
        the message that should be recorded.
    `data`:
        a data dictionary that should be recorded with the event.
    `category`:
        The category for this error. This can be a module name, or just a
        string that clearly identifies the crumb (eg: `http`, `rpc`, etc.)
    `type`:
        can override the type if a special type should be sent to Sentry.

Example:

.. sourcecode:: python

    from raven import breadcrumbs

    breadcrumbs.record(message='This is an important message',
                       category='my_module', level='warning')

Because crumbs go into a ring buffer, often it can be useful to defer
processing of expensive operations until the crumb is actually needed.
For this you can pass a processor which will be passed the data dict for
modifications:

.. sourcecode:: python

    from raven.breadcrumbs import record

    def process_crumb(data):
        data['data'] = compute_expensive_data()

    breadcrumbs.record(message='This is an important message',
                       category='my_module', level='warning',
                       processor=process_crumb)
