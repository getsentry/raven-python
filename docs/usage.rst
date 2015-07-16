Usage
=====

Capture an Error
----------------

::

    from raven import Client

    client = Client('http://dd2c825ff9b1417d88a99573903ebf80:91631495b10b45f8a1cdbc492088da6a@localhost:9000/1')

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()


Adding Context
--------------

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


Testing the Client
------------------

Once you've got your server configured, you can test the Raven client by using its CLI::

  raven test <DSN value>

If you've configured your environment to have SENTRY_DSN available, you can simply drop
the optional DSN argument::

  raven test

You should get something like the following, assuming you're configured everything correctly::

  $ raven test http://dd2c825ff9b1417d88a99573903ebf80:91631495b10b45f8a1cdbc492088da6a@localhost:9000/1
  Using DSN configuration:
    http://dd2c825ff9b1417d88a99573903ebf80:91631495b10b45f8a1cdbc492088da6a@localhost:9000/1

  Client configuration:
    base_url       : http://localhost:9000
    project        : 1
    public_key     : dd2c825ff9b1417d88a99573903ebf80
    secret_key     : 91631495b10b45f8a1cdbc492088da6a

  Sending a test message... success!

  The test message can be viewed at the following URL:
    http://localhost:9000/1/search/?q=c988bf5cb7db4653825c92f6864e7206$b8a6fbd29cc9113a149ad62cf7e0ddd5


Client API
----------

.. autoclass:: raven.base.Client
   :members:
