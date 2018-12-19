Changelog
=========

All notable changes to this project will be documented in this file.
Project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

6.10.0
------

* [Core] Fixed stackframes in some situations being in inverse order.
* [Flask] Fix wrong exception handling logic (accidentally relied on Flask internals).
* [Core] No longer send NaN local vars as non-standard JSON.

6.9.0 (2018-05-30)
------------------
* [Core] Switched from culprit to transaction for automatic transaction reporting.
* [CI] Removed py3.3 from build
* [Django] resolved an issue where the log integration would override the user.

6.8.0 (2018-05-12)
------------------
* [Core] Fixed DSNs without secrets not sending events.
* [Core] Added lazy import for pkg_resources
* [Core] Added NamedTuple Serializer
* [Sanic] Fixed sanic integration dependencies
* [Django] Fixed sql hook bug

6.7.0 (2018-04-18)
------------------
* [Sanic] Added support for sanic.
* [Core] Disabled dill logger by default
* [Core] Added `SENTRY_NAME`, `SENTRY_ENVIRONMENT` and `SENTRY_RELEASE` 
         environment variables
* [Core] DSN secret is now optional
* [Core] Added fix for cases with exceptions in repr
* [core] Fixed bug with mutating `record.data`

6.6.0 (2018-02-12)
------------------
* [Core] Add trimming to breadcrumbs.
* [Core] Improve host message at startup.
* [Core] Update pytest to work on other environments

6.5.0 (2018-01-15)
------------------
* [Core] Fixed missing deprecation on `processors.SanitizePasswordsProcessor`
* [Core] Improve exception handling in `Serializer.transform`
* [Core] Fixed `celery.register_logger_signal` ignoring subclasses
* [Core] Fixed sanitizer skipping `byte` instances
* [Lambda] Fixed `AttributeError` when `requestContext` not present

6.4.0 (2017-12-11)
------------------
* [Core] Support for defining `sanitized_keys` on the client (pr/990)
* [Django] Support for Django 2.0 Urlresolver
* [Docs] Several fixes and improvements

6.3.0 (2017-10-29)
------------------
* [Core] Changed default timeout on http calls to 5 seconds
* [Core] Fixed relative paths for traces generated on Windows
* [Django] Fixed import issues for Django projects < 1.7
* [Django] Fixed django management command data option
* [Django/DRF] Added `application/octet-stream` to non-cacheable types in middleware
* [Django] Added parsing X-Forwarded-For for `user.ip_address`
* [Flask] Added `request.remote_addr` as fallback for ip addresses
* [Lambda] Added initial AWS Lambda support with `contrib.awslambda.LambdaClient` 


6.2.1 (2017-09-21)
------------------

* [Core] Fixed requirements in setup.py


6.2.0 (2017-09-21)
------------------

* [Core] `get_frame_locals` properly using `max_var_size`
* [Core] Fixed raven initialization when `logging._srcfile` is None
* [Core] Fixed import locking to avoid recursion
* [Django] Fixed several issues for Django 1.11 and Django 2.0
* [Django/DRF] Fixed issue with unavailable request data
* [Flask] Added app.logger instrumentation
* [Flask] Added signal on setup_logging
* [ZConfig] Added standalone ZConfig support
* [Celery] Fixed several issues related to Celery


6.1.0 (2017-05-25)
------------------

* Support both string and class values for ``ignore_exceptions`` parameters.
  Class values also support child exceptions.
* Ensure consistent fingerprint for SoftTimeLimitExceeded exceptions
* Add sample_rate configuration
* fix registration of hooks for Django

6.0.0 (2017-02-17)
------------------

* Strip whitespace from DSNs automatically.
* Add `last_event_id` accessor to `Client`.
* Do not require `sys.argv` to be available any more.
* Tags defined on a logging handler will now be merged with individual log record's tags.
* Added explicit support for multidicts in the django client.
* Refactored transports to support multiple URLs.  This might affect
  you if you have custom subclasses of those.  The main change is that
  the URL parameter moved from the constructor into the `send` method.
* Corrected an issue with recursive route resolvers which commonly
  affected things like django-tastyepie.
* Corrected an issue where Django's HTTP request was not always available
  within events.

5.32.0 (2016-11-15)
-------------------

* Made raven python breadcrumb patches work when librato monkey
  patches logging.

5.31.0 (2016-10-21)
-------------------

* Improved fix for the Django middleware regression.

5.30.0 (2016-10-19)
-------------------

* Keep the original type for the django middleware settings if we
  change them.

5.29.0 (2016-10-18)
-------------------

* Added `register_logging_handler`.
* Removed bad mixin from django's WSGI middleware
* Removed "support for extracing data from rest_framework" because
  this broke code.

5.28.0 (2016-10-18)
-------------------

* Corrected an issue that caused `close()` on WSGI iterables to not be
  correctly called.
* Fixes the new Django 1.10 `MIDDLEWARE_CLASSES` warning.

5.27.1 (2016-09-19)
-------------------

* Bugfix for transaction based culprits.

5.27.0 (2016-09-16)
-------------------

* Added support for extracting data from rest_framework in Django integration
* Updated CA bundle.
* Added transaction-based culprits for Celery, Django, and Flask.
* Fixed an issue where ``ignore_exceptions`` wasn't respected.

5.26.0 (2016-08-31)
-------------------

* Fixed potential concurrency issue with event IDs in the Flask integration.
* Added a workaround for leakage when broken WSGI middlware or servers are
  used that do not call `close()` on the iterat.r

5.25.0 (2016-08-23)
-------------------

* Added various improvements for the WSGI and Django support.
* Prevent chained exception recursion
* In environments which look like AWS Lambda or Google App Engine utilize the
  synchronous transport.
* Added Celery config option to ignore expected exceptions
* Improved DSN handling in Flask client.

5.24.0 (2016-08-04)
-------------------

* Added support for Django 1.10.
* Added support for chained exceptions in Python 3.
* Fixed various behavior with handling template errors in Django 1.8+.

5.23.0 (2016-07-14)
-------------------

* Sentry failures now no longer log the failure data in the error
  message.

5.22.0 (2016-07-07)
-------------------

* Fixed template reporting not working for certain versions of Django.

5.21.0 (2016-06-16)
-------------------

* Add formatted attribute to message events
* Fill in empty filename if django fails to give one for
  template information on newer Django versions with disabled
  debug mode.

5.20.0 (2016-06-08)
-------------------

* fixed an error that could cause certain SQL queries to fail to
  record as breadcrumbs if no parameters were supplied.

5.19.0 (2016-05-27)
-------------------

* remove duration from SQL query breadcrumbs. This was not rendered
  in the UI and will come back in future versions of Sentry with a
  different interface.
* resolved a bug that caused crumbs to be recorded incorrectly.

5.18.0 (2016-05-19)
--------------------

* Breadcrumbs are now attempted to be deduplicated to catch some common
  cases where log messages just spam up the breadcrumbs.
* Improvements to the public breadcrumbs API and stabilized some.
* Automatically activate the context on calls to `merge`

5.17.0 (2016-05-14)
-------------------

* if breadcrumbs fail to process due to an error they are now skipped.

5.16.0 (2016-05-09)
-------------------

* exc_info is no longer included in logger based breadcrumbs.
* log the entire logger name as category.
* added a `enable_breadcrumbs` flag to the client to allow the enabling or
  disabling of breadcrumbs quickly.
* corrected an issue where python interpreters with bytecode writing enabled
  would report incorrect logging locations when breadcrumb patching for
  logging was enabled.

5.15.0 (2016-05-03)
-------------------

* Improve thread binding for the context.  This makes the main thread never
  deactivate the client automatically on clear which means that more code
  should automatically support breadcrumbs without changes.

5.14.0 (2016-05-03)
-------------------

* Added support for reading git sha's from packed references.
* Detect disabled thread support for uwsgi.
* Added preliminary support for breadcrumbs.

Note: this version adds breadcrumbs to events.  This means that if you run a
Sentry version older than 8.5 you will see some warnings in the UI.  Consider
using an older version of the client if you do not want to see it.

5.13.0 (2016-04-19)
-------------------

* Resolved an issue where Raven would fail with an exception if the
  package name did not match the setuptools name in some isolated
  cases.

5.12.0 (2016-03-30)
-------------------

* Empty and otherwise falsy (None, False, 0) DSN values are now assumed
  to be equivalent to no DSN being provided.

5.11.2 (2016-03-25)
-------------------

* Added a workaround for back traceback objects passed to raven.  In these
  cases we now wobble further along to at least log something.

5.11.1 (2016-03-07)
-------------------

* The raven client supports the stacktrace to be absent.  This improves support
  with celery and multiprocessing.

5.11.0 (2016-02-29)
-------------------

* ``Client.configure_logging`` has been removed, and handlers will not automatically
  be added to 'sentry' and 'raven' namespaces.
* Improved double error check
* Restored support for exc_info is True.

5.10.2 (2016-01-27)
-------------------

* Remember exceptions in flight until the context is cleared so that two
  reports with the same exception data do not result in two errors
  being logged.
* Allow logging exclusions.

5.10.1 (2016-01-21)
-------------------

* Fixed a problem where bytes as keys in dictionaries caused problems
  on data sanitization if those bytes were outside of the ASCII range.
* Django client no longer requires the user object to be a subclass
  of the base model.
* Corrected an issue with the Django log handler which would cause a recursive import.

5.10.0 (2016-01-14)
-------------------

* Restore template debug support for Django 1.9 and newer.
* Correctly handle SSL verification disabling for newer Python versions.

5.9.2 (2015-12-17)
------------------

* Correct behavior introduced for Django 1.9.

5.9.1 (2015-12-16)
------------------

* Support for isolated apps in Django 1.9.

5.9.0 (2015-12-10)
------------------

* The threaded worker will now correctly handle forking.
* The 'environment' parameter is now supported (requires a Sentry 8.0 server ).
* 'tags' can now be specified as part of a LoggingHandler's constructor.

5.8.0 (2015-10-19)
------------------

* Added support for detecting `release` on Heroku.
* pkg_resources is now prioritized for default version detection.
* Updated `in_app` support to include exception frames.
* Fixed support for `SENTRY_USER_ATTRS` in Flask.
* Handle DSNs which are sent as unicode values in Python 2.

5.7.2 (2015-09-18)
------------------

* Handle passing ``fingerprint`` through logging handler.

5.7.1 (2015-09-16)
------------------

* Correctly handle SHAs in .git/HEAD.
* Fixed several cases of invalid Python3 syntax.

5.7.0 (2015-09-16)
------------------

* Reverted changes to Celery which incorrectly caused some configurations
  to log unwanted messages.
* Improved behavior in ``fetch_git_sha``.
* Removed ``is_authenticated`` property from most integrations.
* Better error handling for errors within Flask context.
* Support for new versions of Flask-Login.
* Update Tornado support for modern versions.
* Update stacktrace truncation code to match current versions of Sentry server.

5.6.0 (2015-08-26)
------------------

* Content is no longer base64-encoded.
* ``fingerprint`` is now correctly supported.
* Django: 1.9 compatibility.
* Celery: Filter ``celery.redirect`` logger.

5.5.0 (2015-07-22)
------------------

* Added ``sys.excepthook`` handler (installed by default).
* Fixed an issue where ``wrap_wsgi`` wasn't being respected.
* Various deprecated code removed.

5.4.4 (2015-07-13)
------------------

* Enforce string-type imports.

5.4.3 (2015-07-12)
------------------

* Python 3 compatibility fixes.

5.4.2 (2015-07-11)
------------------

* Remove scheme checking on transports.
* Added ``SENTRY_TRANSPORT`` to Flask and Django configurations.

5.4.1 (2015-07-08)
------------------

* Fixed packaging of 5.4.0 which erronously kept the ``aiohttp.py`` file in the wheel only.

5.4.0 (2015-07-06)
------------------

* Binding transports via a scheme prefix on DSNs is now deprecated.
* ``raven.conf.load`` has been removed.
* Upstream-related configuration (such as url, project_id, and keys) is now contained in ``RemoteConfig``
  attached to ``Client.remote``
* The ``aiohttp`` transport has been moved to ``raven-aiohttp`` package.

5.3.1 (2015-05-01)
------------------

* Restored support for patching Django's BaseCommand.execute.

5.3.0 (2015-04-30)
------------------

* The UDP transport has been removed.
* The integrated Sentry+Django client has been removed. This is now part of Sentry core.
* Server configuration *must* now be specified with a DSN.
* Upstream errors now have increased verbosity in logs.
* Unsent events now log to 'sentry.errors.uncaught'.
* Django management commands should now effectively autopatch (when run from the CLI).
* Flask wrapper now includes user_context, tags_context, and extra_context helpers.
* Python version is now reported with modules.

5.2.0 (2015-02-11)
------------------

* Protocol version is now 6 (requires Sentry 7.0 or newer).
* Added ``release`` option to Client.
* Added ``fetch_git_sha`` helper.
* Added ``fetch_package_version`` helper.
* Added cookie string sanitizing.
* Added threaded request transport: "threaded+requests+http(s)".

5.1.0 (2014-10-15)
------------------

* Added aiohttp transport.
* Corrected behavior with auto_log_stacks and exceptions.
* Add support for certifi.
* Expanded Flask support.
* Expanded Django support.
* Corrected an issue where processors were not correctly applying.

5.0.0 (2014-05-28)
------------------

* Sentry client protocol is now version 5.
* Various improvements to threaded transport.

4.2.0 (2014-04-14)
------------------

* SSL verification is now on by default.
* Rate limits and other valid API errors are now handled more gracefully.
* Added ``last_event_id`` and ``X-Sentry-ID`` header to Flask.

4.1.0 (2014-03-19)
------------------

* Added verify_ssl option to HTTP transport (defaults to False).
* Added capture_locals option (defaults to True).
* message can now be passed to capture* functions.
* Django <1.4 is no longer supported.
* Function object serialization has been improved.
* SanitizePasswordsProcessor removes API keys.

4.0.0 (2013-12-26)
------------------

* Sentry client protocol is now version 4.

3.6.0 (2013-12-11)
------------------

This changelog does not attempt to account for all changes between 3.6.0 and 3.0.0, but
rather focuses on recent important changes

* Transport modules paths have been refactored.
* The threaded transport is now the default.
* Client.context has changed. Please see documentation for new API.
* Client.user_context was added.
* Client.http_context was added.
* Client.extra_context was added.
* Client.tags_context was added.
* Flask support has been greatly improved.
* raven.contrib.celery.Client has been removed as it was invalid.

3.0.0 (2012-12-27)
------------------

3.0 of Raven requires a Sentry server running at least version 5.1, as it implements
version 3 of the protocol.

Support includes:

* Sending 'python' as the platform.
* The 'tags' option (on all constructors that support options).
* Updated authentication header.

Additionally, the following has changed:

* Configuring the client with an empty DSN value will disable sending of messages.
* All clients should now check ``Client.is_enabled()`` to verify if they should send data.
* ``Client.create_from_text`` and ``Client.create_from_exception`` have been removed.
* ``Client.message`` and ``Client.exception`` have been removed.
* The ``key`` setting has been removed.
* The ``DEBUG`` setting in Django no longer disables Raven.
* The ``register_signals`` option in RAVEN_CONFIG (Django) is no longer used.
* A new helper, ``Client.context()`` is now available for scoping options.
* ``Client.captureExceptions`` is now deprecated in favor of ``Client.context``.
* Credit card values will now be sanitized with the default processors.
* A new eventlet+http transport exists.
* A new threaded+http transport exists.
* PyPy is now supported.
* Django 1.5 should now be supported (experimental).
* Gevent 1.0 should now be supported (experimental).
* Python 2.5 is no longer supported.
* [Django] The ``skip_sentry`` attribute is no longer supported. A new option config option has replaced this: ``SENTRY_IGNORE_EXCEPTIONS``.

2.0.0 (2012-07-05)
------------------

* New serializers exist (and can be registered) against Raven. See ``raven.utils.serializer`` for more information.
* You can now pass ``tags`` to the ``capture`` method. This will require a Sentry server compatible with the new
  tags protocol.
* A new gevent+http transport exists.
* A new tornado+http transport exists.
* A new twisted+http transport exists.
* Zope integration has been added. See docs for more information.
* PasteDeploy integration has been added. See docs for more information.
* A Django endpoint now exists for proxying requests to Sentry. See ``raven.contrib.django.views`` for more information.

1.9.0 (2012-05-23)
------------------

* Signatures are no longer sent with messages. This requires the server version to be at least 4.4.6.
* Several fixes and additions were added to the Django report view.
* ``long`` types are now handled in transform().
* Improved integration with Celery (and django-celery) for capturing errors.

1.8.0 (2012-05-16)
------------------

* There is now a builtin view as part of the Django integration for sending events server-side
  (from the client) to Sentry. The view is currently undocumented, but is available as ``{% url raven-report %}``
  and will use your server side credentials. To use this view you'd simply swap out the servers configuration in
  raven-js and point it to the given URL.
* A new middleware for ZeroRPC now exists.
* A new protocol for registering transports now exists.
* Corrected some behavior in the UDP transport.
* Celery signals are now connected by default within the Django integration.

1.7.0 (2012-04-18)
------------------

* The password sanitizer will now attempt to sanitize key=value pairs within strings (such as the querystring).
* Two new santiziers were added: RemoveStackLocalsProcessor and RemovePostDataProcessor

1.6.0 (2012-04-13)
------------------

* Stacks must now be passed as a list of tuples (frame, lineno) rather than a list of frames. This
  includes calls to logging (extra={'stack': []}), as well as explicit client calls (capture(stack=[])).

  This corrects some issues (mostly in tracebacks) with the wrong lineno being reported for a frame.

1.4.0 (2012-02-05)
------------------

* Raven now tracks the state of the Sentry server. If it receives an error, it will slow down
  requests to the server (by passing them into a named logger, sentry.errors), and increasingly
  delay the next try with repeated failures, up to about a minute.

1.3.6 (2012-02-04)
------------------

* gunicorn is now disabled in default logging configuration

1.3.5 (2012-02-03)
------------------

* Moved exception and message methods to capture{Exception,Message}.
* Added captureQuery method.

1.3.4 (2012-02-02)
------------------

* Corrected duplicate DSN behavior in Django client.

1.3.3 (2012-02-02)
------------------

* Django can now be configured by setting SENTRY_DSN.
* Improve logging for send_remote failures (and correct issue created when
  send_encoded was introduced).
* Renamed SantizePassworsProcessor to SanitizePassworsProcessor.

1.3.2 (2012-02-01)
------------------

* Support sending the culprit with logging messages as part of extra.

1.3.1 (2012-02-01)
-------------

* Added client.exception and client.message shortcuts.

1.3.0 (2012-01-31)
------------------

* Refactored client send API to be more easily extensible.
* MOAR TESTS!

1.2.2 (2012-01-31)
------------------

* Gracefully handle exceptions in Django client when using integrated
  setup.
* Added Client.error_logger as a new logger instance that points to
  ``sentry.errors``.

1.2.1 (2012-01-31)
------------------

* Corrected behavior with raven logging errors to send_remote
  which could potentially cause a very large backlog to Sentry
  when it should just log to ``sentry.errors``.
* Ensure the ``site`` argument is sent to the server.

1.2.0 (2012-01-30)
------------------

* Made DSN a first-class citizen throughout Raven.
* Added a Pylons-specific WSGI middleware.
* Improved the generic WSGI middleware to capture HTTP information.
* Improved logging and logbook handlers.

1.1.6 (2012-01-26)
------------------

* Corrected logging stack behavior so that it doesnt capture raven+logging
  extensions are part of the frames.

1.1.5 (2012-01-25)
------------------

* Remove logging attr magic.

1.1.4 (2012-01-25)
------------------

* Correct encoding behavior on bool and float types.

1.1.3 (2012-01-25)
------------------

* Fix 'request' attribute on Django logging.

1.1.2 (2012-01-24)
------------------

* Corrected logging behavior with extra data to match pre 1.x behavior.

1.1.1 (2012-01-23)
------------------

* Handle frames that are missing f_globals and f_locals.
* Stricter conversion of int and boolean values.
* Handle invalid sources for templates in Django.

1.1.0 (2012-01-23)
------------------

* varmap was refactored to send keys back to callbacks.
* SanitizePasswordProcessor now handles http data.

1.0.5 (2012-01-18)
------------------

* Renaming raven2 to raven as it causes too many issues.

1.0.4 (2012-01-18)
------------------

* Corrected a bug in setup_logging.
* Raven now sends "sentry_version" header which is the expected
  server version.

1.0.3 (2012-01-17)
------------------

* Handle more edge cases on stack iteration.

1.0.2 (2012-01-17)
------------------

* Gracefully handle invalid f_locals.

1.0.1 (2012-01-15)
------------------

* All datetimes are assumed to be utcnow() as of Sentry 2.0.0-RC5

1.0.0 (2012-01-15)
------------------

* Now only works with Sentry>=2.0.0 server.
* Raven is now listed as raven2 on PyPi.

0.8.0 (XXXX-XX-XX)
------------------

* raven.contrib.celery is now useable.
* raven.contrib.django.celery is now useable.
* Fixed a bug with request.raw_post_data buffering in Django.

0.7.1 (2011-10-24)
------------------

* Servers would stop iterating after the first successful post which was not the
  intended behavior.

0.7.0 (2011-10-24)
------------------

* You can now explicitly pass a list of frame objects to the process method.

0.6.1 (2011-10-19)
------------------

* The default logging handler (SentryHandler) will now accept a set of kwargs to instantiate
  a new client with (GH-10).
* Fixed a bug with checksum generation when module or function were missing (GH-9).

0.6.0 (2011-10-19)
------------------

* Added a Django-specific WSGI middleware.

0.5.1 (2011-10-17)
------------------

* Two minor fixes for the Django client:
* Ensure the __sentry__ key exists in data in (GH-8).
* properly set kwargs['data'] to an empty list when its a NoneType (GH-6).

0.5.0 (2011-10-14)
------------------

* Require ``servers`` on base Client.
* Added support for the ``site`` option in Client.
* Moved raven.contrib.django.logging to raven.contrib.django.handlers.

0.4.0 (2011-10-11)
------------------

* Fixed an infinite loop in iter_tb.

0.3.0 (2011-10-11)
------------------

* Removed the ``thrashed`` key in ``request.sentry`` for the Django integration.
* Changed the logging handler to correctly inherit old-style classes (GH-1).
* Added a ``client`` argument to ``raven.contrib.django.models.get_client()``.

0.2.0 (2011-10-10)
------------------

* auto_log_stacks now works with create_from_text
* added Client.get_ident

0.1.0 (XXXX-XX-XX)
------------------

* Initial version of Raven (extracted from django-sentry 1.12.1).
