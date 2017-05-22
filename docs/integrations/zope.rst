Zope/Plone
==========

zope.conf
---------

Zope has extensible logging configuration options.
A basic instance (not ZEO client) setup for logging looks like this:

.. code-block:: xml

  <eventlog>
    level INFO
    <logfile>
     path ${buildout:directory}/var/{:_buildout_section_name_}.log
     level INFO
    </logfile>

    %import raven.contrib.zope
    <sentry>
      dsn ___DSN___
      level ERROR
    </sentry>
  </eventlog>

This configuration retains normal logging to a logfile, but adds
Sentry logging for ERRORs.

All options of :py:class:`raven.base.Client` are supported.

Use a buildout recipe instead of editing zope.conf directly.
To add the equivalent instance configuration, you would do this:

.. code-block:: ini

    [instance]
    recipe = plone.recipe.zope2instance
    ...
    event-log-custom =
        %import raven.contrib.zope
        <logfile>
          path ${buildout:directory}/var/instance.log
          level INFO
        </logfile>
        <sentry>
          dsn ___DSN___
          level ERROR
        </sentry>

To add the equivalent ZEO client configuration, you would do this:

.. code-block:: ini

    [instance]
    recipe = plone.recipe.zope2instance
    ...
    event-log-custom =
        %import raven.contrib.zope
        <logfile>
          path ${buildout:var-dir}/${:_buildout_section_name_}/event.log
          level INFO
        </logfile>
        <sentry>
          dsn ___DSN___
          level ERROR
        </sentry>
