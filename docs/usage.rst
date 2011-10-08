Usage
=====

TODO :)

::

    from raven import Client

    client = Client(servers=['http://sentry.local/store/'])

    try:
        ...
    except:
        client.create_from_exception()
        raise