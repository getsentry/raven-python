Configuring Celery
==================

Celery provides a hook for catching task failures, and Raven can easily plug into that hook::

    from raven.contrib.celery import register_signal

    register_signal(client)

If you're using Django and ``djcelery`` exists in your ``INSTALLED_APPS``, we've already set this up for you.
