"""
raven.base
~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import base64
import zlib
import logging
import os
import sys
import time
import uuid
import warnings

from datetime import datetime

import raven
from raven.conf import defaults
from raven.context import Context
from raven.utils import six, json, get_versions, get_auth_header, merge_dicts
from raven.utils.encoding import to_unicode
from raven.utils.serializer import transform
from raven.utils.stacks import get_stack_info, iter_stack_frames, get_culprit
from raven.utils.urlparse import urlparse
from raven.utils.compat import HTTPError
from raven.transport.registry import TransportRegistry, default_transports

__all__ = ('Client',)

PLATFORM_NAME = 'python'

# singleton for the client
Raven = None


class ModuleProxyCache(dict):
    def __missing__(self, key):
        module, class_name = key.rsplit('.', 1)

        handler = getattr(__import__(
            module, {}, {}, [class_name]), class_name)

        self[key] = handler

        return handler


class ClientState(object):
    ONLINE = 1
    ERROR = 0

    def __init__(self):
        self.status = self.ONLINE
        self.last_check = None
        self.retry_number = 0

    def should_try(self):
        if self.status == self.ONLINE:
            return True

        interval = min(self.retry_number, 6) ** 2

        if time.time() - self.last_check > interval:
            return True

        return False

    def set_fail(self):
        self.status = self.ERROR
        self.retry_number += 1
        self.last_check = time.time()

    def set_success(self):
        self.status = self.ONLINE
        self.last_check = None
        self.retry_number = 0

    def did_fail(self):
        return self.status == self.ERROR


class Client(object):
    """
    The base Raven client, which handles both local direct
    communication with Sentry (through the GroupedMessage API), as
    well as communicating over the HTTP API to multiple servers.

    Will read default configuration from the environment variable
    ``SENTRY_DSN`` if available.

    >>> from raven import Client

    >>> # Read configuration from ``os.environ['SENTRY_DSN']``
    >>> client = Client()

    >>> # Specify a DSN explicitly
    >>> client = Client(dsn='https://public_key:secret_key@sentry.local/project_id')

    >>> # Record an exception
    >>> try:
    >>>     1/0
    >>> except ZeroDivisionError:
    >>>     ident = client.get_ident(client.captureException())
    >>>     print "Exception caught; reference is %s" % ident
    """
    logger = logging.getLogger('raven')
    protocol_version = '4'

    _registry = TransportRegistry(transports=default_transports)

    def __init__(self, dsn=None, **options):
        global Raven

        o = options

        self.configure_logging()

        # configure loggers first
        cls = self.__class__
        self.state = ClientState()
        self.logger = logging.getLogger(
            '%s.%s' % (cls.__module__, cls.__name__))
        self.error_logger = logging.getLogger('sentry.errors')

        if dsn is None and os.environ.get('SENTRY_DSN'):
            msg = "Configuring Raven from environment variable 'SENTRY_DSN'"
            self.logger.debug(msg)
            dsn = os.environ['SENTRY_DSN']

        if dsn:
            # TODO: should we validate other options werent sent?
            urlparts = urlparse(dsn)
            self.logger.debug(
                "Configuring Raven for host: %s://%s:%s" % (urlparts.scheme,
                urlparts.netloc, urlparts.path))
            dsn_config = raven.load(dsn, transport_registry=self._registry)
            servers = dsn_config['SENTRY_SERVERS']
            project = dsn_config['SENTRY_PROJECT']
            public_key = dsn_config['SENTRY_PUBLIC_KEY']
            secret_key = dsn_config['SENTRY_SECRET_KEY']
            transport_options = dsn_config.get('SENTRY_TRANSPORT_OPTIONS', {})
        else:
            if o.get('servers'):
                warnings.warn('Manually configured connections are deprecated. Switch to a DSN.', DeprecationWarning)
            servers = o.get('servers')
            project = o.get('project')
            public_key = o.get('public_key')
            secret_key = o.get('secret_key')
            transport_options = {}

        self.servers = servers
        self.public_key = public_key
        self.secret_key = secret_key
        self.project = project or defaults.PROJECT
        self.transport_options = transport_options

        self.include_paths = set(o.get('include_paths') or [])
        self.exclude_paths = set(o.get('exclude_paths') or [])
        self.name = six.text_type(o.get('name') or defaults.NAME)
        self.auto_log_stacks = bool(
            o.get('auto_log_stacks') or defaults.AUTO_LOG_STACKS)
        self.string_max_length = int(
            o.get('string_max_length') or defaults.MAX_LENGTH_STRING)
        self.list_max_length = int(
            o.get('list_max_length') or defaults.MAX_LENGTH_LIST)
        self.site = o.get('site', defaults.SITE)
        self.include_versions = o.get('include_versions', True)
        self.processors = o.get('processors')
        if self.processors is None:
            self.processors = defaults.PROCESSORS

        context = o.get('context')
        if context is None:
            context = {'sys.argv': sys.argv[:]}
        self.extra = context
        self.tags = o.get('tags') or {}

        self.module_cache = ModuleProxyCache()

        # servers may be set to a NoneType (for Django)
        if not self.is_enabled():
            self.logger.info(
                'Raven is not configured (logging is disabled). Please see the'
                ' documentation for more information.')

        if Raven is None:
            Raven = self

        self._context = Context()

    @classmethod
    def register_scheme(cls, scheme, transport_class):
        cls._registry.register_scheme(scheme, transport_class)

    def configure_logging(self):
        for name in ('raven', 'sentry'):
            logger = logging.getLogger(name)
            if logger.handlers:
                continue
            logger.addHandler(logging.StreamHandler())
            logger.setLevel(logging.INFO)

    def get_processors(self):
        for processor in self.processors:
            yield self.module_cache[processor](self)

    def get_module_versions(self):
        if not self.include_versions:
            return {}
        return get_versions(self.include_paths)

    def get_ident(self, result):
        """
        Returns a searchable string representing a message.

        >>> result = client.process(**kwargs)
        >>> ident = client.get_ident(result)
        """
        return '$'.join(result)

    def get_handler(self, name):
        return self.module_cache[name](self)

    def _get_public_dsn(self):
        url = urlparse(self.servers[0])
        netloc = url.hostname
        if url.port:
            netloc += ':%s' % url.port
        path = url.path.replace('api/%s/store/' % (self.project,), self.project)
        return '//%s@%s%s' % (self.public_key, netloc, path)

    def get_public_dsn(self, scheme=None):
        """
        Returns a public DSN which is consumable by raven-js

        >>> # Return scheme-less DSN
        >>> print client.get_public_dsn()

        >>> # Specify a scheme to use (http or https)
        >>> print client.get_public_dsn('https')
        """
        if not self.is_enabled():
            return
        url = self._get_public_dsn()
        if not scheme:
            return url
        return '%s:%s' % (scheme, url)

    def build_msg(self, event_type, data=None, date=None,
                  time_spent=None, extra=None, stack=None, public_key=None,
                  tags=None, **kwargs):
        """
        Captures, processes and serializes an event into a dict object

        The result of ``build_msg`` should be a standardized dict, with
        all default values available.
        """

        # create ID client-side so that it can be passed to application
        event_id = uuid.uuid4().hex

        data = merge_dicts(self.context.data, data)

        data.setdefault('tags', {})
        data.setdefault('extra', {})
        data.setdefault('level', logging.ERROR)

        if stack is None:
            stack = self.auto_log_stacks

        if '.' not in event_type:
            # Assume it's a builtin
            event_type = 'raven.events.%s' % event_type

        handler = self.get_handler(event_type)
        result = handler.capture(**kwargs)

        # data (explicit) culprit takes over auto event detection
        culprit = result.pop('culprit', None)
        if data.get('culprit'):
            culprit = data['culprit']

        for k, v in six.iteritems(result):
            if k not in data:
                data[k] = v

        if stack and 'sentry.interfaces.Stacktrace' not in data:
            if stack is True:
                frames = iter_stack_frames()

            else:
                frames = stack

            data.update({
                'sentry.interfaces.Stacktrace': {
                    'frames': get_stack_info(frames,
                        transformer=self.transform)
                },
            })

        if 'sentry.interfaces.Stacktrace' in data:
            if self.include_paths:
                for frame in data['sentry.interfaces.Stacktrace']['frames']:
                    if frame.get('in_app') is not None:
                        continue

                    path = frame.get('module')
                    if not path:
                        continue

                    if path.startswith('raven.'):
                        frame['in_app'] = False
                    else:
                        frame['in_app'] = (
                            any(path.startswith(x) for x in self.include_paths)
                            and not
                            any(path.startswith(x) for x in self.exclude_paths)
                        )

        if not culprit:
            if 'sentry.interfaces.Stacktrace' in data:
                culprit = get_culprit(data['sentry.interfaces.Stacktrace']['frames'])
            elif data.get('sentry.interfaces.Exception', {}).get('stacktrace'):
                culprit = get_culprit(data['sentry.interfaces.Exception']['stacktrace']['frames'])

        if not data.get('level'):
            data['level'] = kwargs.get('level') or logging.ERROR

        if not data.get('server_name'):
            data['server_name'] = self.name

        if not data.get('modules'):
            data['modules'] = self.get_module_versions()

        data['tags'] = merge_dicts(self.tags, data['tags'], tags)
        data['extra'] = merge_dicts(self.extra, data['extra'], extra)

        # Legacy support for site attribute
        site = data.pop('site', None) or self.site
        if site:
            data['tags'].setdefault('site', site)

        if culprit:
            data['culprit'] = culprit

        # Run the data through processors
        for processor in self.get_processors():
            data.update(processor.process(data))

        if 'message' not in data:
            data['message'] = handler.to_string(data)

        # tags should only be key=>u'value'
        for key, value in six.iteritems(data['tags']):
            data['tags'][key] = to_unicode(value)

        # extra data can be any arbitrary value
        for k, v in six.iteritems(data['extra']):
            data['extra'][k] = self.transform(v)

        # It's important date is added **after** we serialize
        data.setdefault('project', self.project)
        data.setdefault('timestamp', date or datetime.utcnow())
        data.setdefault('time_spent', time_spent)
        data.setdefault('event_id', event_id)
        data.setdefault('platform', PLATFORM_NAME)

        return data

    def transform(self, data):
        return transform(
            data, list_max_length=self.list_max_length,
            string_max_length=self.string_max_length)

    @property
    def context(self):
        """
        Updates this clients thread-local context for future events.

        >>> def view_handler(view_func, *args, **kwargs):
        >>>     client.context.merge(tags={'key': 'value'})
        >>>     try:
        >>>         return view_func(*args, **kwargs)
        >>>     finally:
        >>>         client.context.clear()
        """
        return self._context

    def user_context(self, data):
        """
        Update the user context for future events.

        >>> client.user_context({'email': 'foo@example.com'})
        """
        return self.context.merge({
            'sentry.interfaces.User': data,
        })

    def http_context(self, data, **kwargs):
        """
        Update the http context for future events.

        >>> client.http_context({'url': 'http://example.com'})
        """
        return self.context.merge({
            'sentry.interfaces.Http': data,
        })

    def extra_context(self, data, **kwargs):
        """
        Update the extra context for future events.

        >>> client.extra_context({'foo': 'bar'})
        """
        return self.context.merge({
            'extra': data,
        })

    def tags_context(self, data, **kwargs):
        """
        Update the tags context for future events.

        >>> client.tags_context({'version': '1.0'})
        """
        return self.context.merge({
            'tags': data,
        })

    def capture(self, event_type, data=None, date=None, time_spent=None,
                extra=None, stack=None, tags=None, **kwargs):
        """
        Captures and processes an event and pipes it off to SentryClient.send.

        To use structured data (interfaces) with capture:

        >>> capture('raven.events.Message', message='foo', data={
        >>>     'sentry.interfaces.Http': {
        >>>         'url': '...',
        >>>         'data': {},
        >>>         'query_string': '...',
        >>>         'method': 'POST',
        >>>     },
        >>>     'logger': 'logger.name',
        >>> }, extra={
        >>>     'key': 'value',
        >>> })

        The finalized ``data`` structure contains the following (some optional)
        builtin values:

        >>> {
        >>>     # the culprit and version information
        >>>     'culprit': 'full.module.name', # or /arbitrary/path
        >>>
        >>>     # all detectable installed modules
        >>>     'modules': {
        >>>         'full.module.name': 'version string',
        >>>     },
        >>>
        >>>     # arbitrary data provided by user
        >>>     'extra': {
        >>>         'key': 'value',
        >>>     }
        >>> }

        :param event_type: the module path to the Event class. Builtins can use
                           shorthand class notation and exclude the full module
                           path.
        :param data: the data base, useful for specifying structured data
                           interfaces. Any key which contains a '.' will be
                           assumed to be a data interface.
        :param date: the datetime of this event
        :param time_spent: a integer value representing the duration of the
                           event (in milliseconds)
        :param event_id: a 32-length unique string identifying this event
        :param extra: a dictionary of additional standard metadata
        :param culprit: a string representing the cause of this event
                        (generally a path to a function)
        :return: a 32-length string identifying this event
        """

        if not self.is_enabled():
            return

        data = self.build_msg(
            event_type, data, date, time_spent, extra, stack, tags=tags,
            **kwargs)

        self.send(**data)

        return (data.get('event_id'),)

    def _get_log_message(self, data):
        # decode message so we can show the actual event
        try:
            data = self.decode(data)
        except:
            message = '<failed decoding data>'
        else:
            message = data.pop('message', '<no message value>')
        return message

    def is_enabled(self):
        """
        Return a boolean describing whether the client should attempt to send
        events.
        """
        return bool(self.servers)

    def _successful_send(self):
        self.state.set_success()

    def _failed_send(self, e, url, data):
        if isinstance(e, HTTPError):
            body = e.read()
            self.error_logger.error(
                'Unable to reach Sentry log server: %s (url: %s, body: %s)',
                e, url, body, exc_info=True,
                extra={'data': {'body': body[:200], 'remote_url': url}})
        else:
            self.error_logger.error(
                'Unable to reach Sentry log server: %s (url: %s)', e, url,
                exc_info=True, extra={'data': {'remote_url': url}})

        message = self._get_log_message(data)
        self.error_logger.error('Failed to submit message: %r', message)
        self.state.set_fail()

    def send_remote(self, url, data, headers=None):
        if headers is None:
            headers = {}
        if not self.state.should_try():
            message = self._get_log_message(data)
            self.error_logger.error(message)
            return

        self.logger.debug('Sending message of length %d to %s', len(data), url)

        def failed_send(e):
            self._failed_send(e, url, data)

        try:
            parsed = urlparse(url)
            transport = self._registry.get_transport(
                parsed, **self.transport_options)
            if transport.async:
                transport.async_send(data, headers, self._successful_send,
                                     failed_send)
            else:
                transport.send(data, headers)
                self._successful_send()
        except Exception as e:
            failed_send(e)

    def send(self, auth_header=None, **data):
        """
        Serializes the message and passes the payload onto ``send_encoded``.
        """
        message = self.encode(data)

        return self.send_encoded(message, auth_header=auth_header)

    def send_encoded(self, message, auth_header=None, **kwargs):
        """
        Given an already serialized message, signs the message and passes the
        payload off to ``send_remote`` for each server specified in the servers
        configuration.
        """
        client_string = 'raven-python/%s' % (raven.VERSION,)

        if not auth_header:
            timestamp = time.time()
            auth_header = get_auth_header(
                protocol=self.protocol_version,
                timestamp=timestamp,
                client=client_string,
                api_key=self.public_key,
                api_secret=self.secret_key,
            )

        for url in self.servers:
            headers = {
                'User-Agent': client_string,
                'X-Sentry-Auth': auth_header,
                'Content-Type': 'application/octet-stream',
            }

            self.send_remote(url=url, data=message, headers=headers)

    def encode(self, data):
        """
        Serializes ``data`` into a raw string.
        """
        return base64.b64encode(zlib.compress(json.dumps(data).encode('utf8')))

    def decode(self, data):
        """
        Unserializes a string, ``data``.
        """
        return json.loads(zlib.decompress(base64.b64decode(data)).decode('utf8'))

    def captureMessage(self, message, **kwargs):
        """
        Creates an event from ``message``.

        >>> client.captureMessage('My event just happened!')
        """
        return self.capture('raven.events.Message', message=message, **kwargs)

    def captureException(self, exc_info=None, **kwargs):
        """
        Creates an event from an exception.

        >>> try:
        >>>     exc_info = sys.exc_info()
        >>>     client.captureException(exc_info)
        >>> finally:
        >>>     del exc_info

        If exc_info is not provided, or is set to True, then this method will
        perform the ``exc_info = sys.exc_info()`` and the requisite clean-up
        for you.

        ``kwargs`` are passed through to ``.capture``.
        """
        return self.capture(
            'raven.events.Exception', exc_info=exc_info, **kwargs)

    def captureQuery(self, query, params=(), engine=None, **kwargs):
        """
        Creates an event for a SQL query.

        >>> client.captureQuery('SELECT * FROM foo')
        """
        return self.capture(
            'raven.events.Query', query=query, params=params, engine=engine,
            **kwargs)

    def captureExceptions(self, **kwargs):
        warnings.warn(
            'captureExceptions is deprecated, used context() instead.',
            DeprecationWarning)
        return self.context(**kwargs)


class DummyClient(Client):
    "Sends messages into an empty void"
    def send(self, **kwargs):
        return None
