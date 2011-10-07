Usage
=====

TODO :)

::

    from raven import Client

    client = Client(remote_urls=['http://sentry.local/store/'])

    try:
        ...
    except:
        client.create_from_exception()
        raise