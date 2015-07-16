API Reference
=============

.. default-domain:: py

This gives you an overview of the public API that raven-python exposes.


Client
------

.. py:class:: raven.Client(dsn=None, **kwargs)

    The client needs to be instanciated once and can then be used for
    submitting events to the Sentry server.  For information about the
    configuration of that client and which parameters are accepted see
    :ref:`python-client-config`.

    .. py:method:: capture(event_type, data=None, date=None, \
           time_spent=None, extra=None, stack=False, tags=None, **kwargs)

        This method is the low-level method for reporting events to
        Sentry.  It captures and processes an event and pipes it via the
        configured transport to Sentry.

        Example::

            capture('raven.events.Message', message='foo', data={
                'request': {
                    'url': '...',
                    'data': {},
                    'query_string': '...',
                    'method': 'POST',
                },
                'logger': 'logger.name',
            }, extra={
                'key': 'value',
            })

        :param event_type: the module path to the Event class. Builtins can
                           use shorthand class notation and exclude the
                           full module path.
        :param data: the data base, useful for specifying structured data
                           interfaces. Any key which contains a '.' will be
                           assumed to be a data interface.
        :param date: the datetime of this event.  If not supplied the
                     current timestamp is used.
        :param time_spent: a integer value representing the duration of the
                           event (in milliseconds)
        :param extra: a dictionary of additional standard metadata.
        :param stack: If set to `True` a stack frame is recorded together
                      with the event.
        :param tags: list of extra tags
        :param kwargs: extra keyword arguments are handled specific to the
                       reported event type.
        :return: a tuple with a 32-length string identifying this event

    .. py:method:: captureMessage(message, **kwargs)

        This is a shorthand to reporting a message via :meth:`capture`.
        It passes ``'raven.events.Message'`` as `event_type` and the
        message along.  All other keyword arguments are regularly
        forwarded.

        Example::

            client.captureMessage('This just happened!')

    .. py:method:: captureException(message, exc_info=None, **kwargs)

        This is a shorthand to reporting an exception via :meth:`capture`.
        It passes ``'raven.events.Exception'`` as `event_type` and the
        traceback along.  All other keyword arguments are regularly
        forwarded.

        If exc_info is not provided, or is set to True, then this method
        will perform the ``exc_info = sys.exc_info()`` and the requisite
        clean-up for you.

        Example::

            try:
                1 / 0
            except Exception:
                client.captureException()

    .. py:method:: send(**data)

        Accepts all data parameters and serializes them, then sends then
        onwards via the transport to Sentry.  This can be used as to send
        low-level protocol data to the server.

    .. py:attribute:: context

        Returns a reference to the thread local context object.  See
        :py:class:`raven.context.Context` for more information.

Context
-------

.. py:class:: raven.context.Context()

    The context object works similar to a dictionary and is used to record
    information that should be submitted with events automatically.  It is
    available through :py:attr:`raven.Client.context` and is thread local.
    This means that you can modify this object over time to feed it with
    more appropriate information.

    .. py:method:: merge(data)

        Performs a merge of the current data in the context and the new
        data provided.

    .. py:method:: clear()

        Clears the context.  It's important that you make sure to call
        this when you reuse the thread for something else.  For instance
        for web frameworks it's generally a good idea to call this at the
        end of the HTTP request.

        Otherwise you run at risk of seeing incorrect information after
        the first use of the thread.
