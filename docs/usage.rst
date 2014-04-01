.. _usage-label:

Capture an Error
================

::

    from raven import Client

    client = Client('http://dd2c825ff9b1417d88a99573903ebf80:91631495b10b45f8a1cdbc492088da6a@localhost:9000/1')

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()


Adding Context
==============

A few helpers exist for adding context to a request. These are most useful within a middleware, or some kind of context wrapper.

::

    # If you're using the Django client, we already deal with this for you.
    class DjangoUserContext(object):
        def process_request(self, request):
            client.user_context({
                'email': request.user.email,
            })

        def process_response(self, request):
            client.context.clear()


See also:

- Client.extra_context
- Client.http_context
- Client.tags_context


Client API
==========

.. autoclass:: raven.base.Client
   :members:
