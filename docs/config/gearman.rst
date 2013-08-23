Configuring Gearman
===================

Gearman provides a generic application framework to farm out work to other machines or processes that are better
suited to do the work. It allows you to do work in parallel, to load balance processing, and to call functions
between languages. For more information visit http://gearman.org/.

In order to use gearman support in raven, you have to have installed gearmand job server on your machine.

If you're using Django add this to your ``settings``::

    GEARMAN_SERVERS = ['127.0.0.1:4730']
    SENTRY_CLIENT = 'raven.contrib.django.gearman.GearmanClient'
    SENTRY_GEARMAN_CLIENT = 'raven.contrib.django.client.DjangoClient'


Next you need to run ``raven_gearman`` worker to process your logging events in the background::

    $ python manage.py raven_gearman


``raven_gearman`` command is build on top of django-gearman-commands app. For more information about
setting-up your worker please have a look at this url https://github.com/CodeScaleInc/django-gearman-commands.


How does it work ?
------------------

All logging events as submitted as job to gearmand job server. They are not submitted directly to the sentry server.
``raven_gearman`` is running in background and downloads jobs from gearmand job server. Every downloaded job is then
transformed into raven event and sent by ``SENTRY_GEARMAN_CLIENT`` to sentry server. The point is, that all this happens
asynchronously and don't block your application main thread.