Integrations
============

The Raven Python module also comes with integration for some commonly used
libraries to automatically capture errors from common environments.  This
means that once you have such an integration configured you typically do
not need to report errors manually.

Some integrations allow specifying these in a standard configuration,
otherwise they are generally passed upon instantiation of the Sentry
client.

.. toctree::
   :maxdepth: 1

   bottle
   celery
   django
   flask
   logbook
   logging
   pylons
   pyramid
   rq
   tornado
   wsgi
   zerorpc
   zope
