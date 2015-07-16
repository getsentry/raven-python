Zope/Plone
==========

zope.conf
---------

Zope has extensible logging configuration options.
A basic setup for logging looks like that:

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

This configuration keeps the regular logging to a logfile, but adds
logging to sentry for ERRORs.

All options of :py:class:`raven.base.Client` are supported.

Nobody writes zope.conf files these days, instead buildout recipe does
that.  To add the equivalent configuration, you would do this:

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
