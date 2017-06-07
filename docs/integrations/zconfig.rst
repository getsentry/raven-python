ZConfig logging configuration
=============================

`ZConfig
<http://zconfig.readthedocs.io/en/latest/using-logging.html>`_
provides one of the most powerful clean configuration mechanism for
the Python logging module.  To learn more, see:

  http://zconfig.readthedocs.io/en/latest/using-logging.html

To use with sentry, use the sentry handler tag:

.. code-block:: xml

  <logger>
    level INFO
    <logfile>
     path ${buildout:directory}/var/{:_buildout_section_name_}.log
     level INFO
    </logfile>

    %import raven.contrib.zconfig
    <sentry>
      dsn ___DSN___
      level ERROR
    </sentry>
  </logger>

This configuration retains normal logging to a logfile, but adds
Sentry logging for ERRORs.

All options of :py:class:`raven.base.Client` are supported.
