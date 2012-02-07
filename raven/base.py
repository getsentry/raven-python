"""
raven.base
~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import base64
import datetime
import hashlib
import logging
import os
import time
import urllib2
import uuid
import warnings
from urlparse import urlparse
from socket import socket, AF_INET, SOCK_DGRAM, error as socket_error

import raven
from raven.conf import defaults
from raven.utils import json, varmap, get_versions, get_signature, get_auth_header
from raven.utils.encoding import transform, shorten, to_unicode
from raven.utils.stacks import get_stack_info, iter_stack_frames, \
  get_culprit


class ModuleProxyCache(dict):
    def __missing__(self, key):
        module, class_name = key.rsplit('.', 1)

        handler = getattr(__import__(module, {}, {}, [class_name], -1), class_name)

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

        interval = min(self.retry_number, 6)**2

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


class Client(object):
    """
    The base Raven client, which handles both local direct communication with Sentry (through
    the GroupedMessage API), as well as communicating over the HTTP API to multiple servers.

    Will read default configuration from the environment variable ``SENTRY_DSN``
    if available.

    >>> from raven import Client

    >>> # Read configuration from ``os.environ['SENTRY_DSN']``
    >>> client = Client()

    >>> # Specify a DSN explicitly
    >>> client = Client(dsn='https://public_key:secret_key@sentry.local/project_id')

    >>> # Configure the client manually
    >>> client = Client(
    >>>     servers=['http://sentry.local/api/store/'],
    >>>     include_paths=['my.package'],
    >>>     project='project_id',
    >>>     public_key='public_key',
    >>>     secret_key='secret_key',
    >>> )

    >>> # Record an exception
    >>> try:
    >>>     1/0
    >>> except ZeroDivisionError:
    >>>     ident = client.get_ident(client.captureException())
    >>>     print "Exception caught; reference is %%s" %% ident
    """
    logger = logging.getLogger('raven')
    protocol_version = '2.0'

    def __init__(self, servers=None, include_paths=None, exclude_paths=None, timeout=None,
                 name=None, auto_log_stacks=None, key=None, string_max_length=None,
                 list_max_length=None, site=None, public_key=None, secret_key=None,
                 processors=None, project=None, dsn=None, **kwargs):
        # configure loggers first
        cls = self.__class__
        self.state = ClientState()
        self.logger = logging.getLogger('%s.%s' % (cls.__module__, cls.__name__))
        self.error_logger = logging.getLogger('sentry.errors')

        if isinstance(servers, basestring):
            # must be a DSN:
            if dsn:
                raise ValueError("You seem to be incorrectly instantiating the raven Client class.")
            dsn = servers
            servers = None

        if dsn is None and os.environ.get('SENTRY_DSN'):
            self.logger.info("Configuring Raven from environment variable 'SENTRY_DSN'")
            dsn = os.environ['SENTRY_DSN']

        if dsn:
            # TODO: should we validate other options werent sent?
            self.logger.info("Configuring Raven from DSN: %r", dsn)
            options = raven.load(dsn)
            servers = options['SENTRY_SERVERS']
            project = options['SENTRY_PROJECT']
            public_key = options['SENTRY_PUBLIC_KEY']
            secret_key = options['SENTRY_SECRET_KEY']

        # servers may be set to a NoneType (for Django)
        if servers and not (key or (secret_key and public_key)):
            raise TypeError('Missing configuration for client. Please see documentation.')

        self.servers = servers
        self.include_paths = set(include_paths or defaults.INCLUDE_PATHS)
        self.exclude_paths = set(exclude_paths or defaults.EXCLUDE_PATHS)
        self.timeout = int(timeout or defaults.TIMEOUT)
        self.name = unicode(name or defaults.NAME)
        self.auto_log_stacks = bool(auto_log_stacks or defaults.AUTO_LOG_STACKS)
        self.key = str(key or defaults.KEY)
        self.string_max_length = int(string_max_length or defaults.MAX_LENGTH_STRING)
        self.list_max_length = int(list_max_length or defaults.MAX_LENGTH_LIST)
        if (site or defaults.SITE):
            self.site = unicode(site or defaults.SITE)
        else:
            self.site = None
        self.public_key = public_key
        self.secret_key = secret_key
        self.project = int(project or defaults.PROJECT)

        self.processors = processors or defaults.PROCESSORS
        self.module_cache = ModuleProxyCache()
        self.udp_socket = None

    def get_processors(self):
        for processor in self.processors:
            yield self.module_cache[processor](self)

    def get_ident(self, result):
        """
        Returns a searchable string representing a message.

        >>> result = client.process(**kwargs)
        >>> ident = client.get_ident(result)
        """
        return '$'.join(result)

    def get_handler(self, name):
        return self.module_cache[name](self)

    def capture(self, event_type, data=None, date=None, time_spent=None, event_id=None,
                extra=None, stack=None, **kwargs):
        """
        Captures and processes an event and pipes it off to SentryClient.send.

        To use structured data (interfaces) with capture:

        >>> capture('Message', message='foo', data={
        >>>     'sentry.interfaces.Http': {
        >>>         'url': '...',
        >>>         'data': {},
        >>>         'query_string': '...',
        >>>         'method': 'POST',
        >>>     },
        >>>     'logger': 'logger.name',
        >>>     'site': 'site.name',
        >>> }, extra={
        >>>     'key': 'value',
        >>> })

        The finalized ``data`` structure contains the following (some optional) builtin values:

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

        :param event_type: the module path to the Event class. Builtins can use shorthand class
                           notation and exclude the full module path.
        :param tags: a list of tuples (key, value) specifying additional tags for event
        :param data: the data base, useful for specifying structured data interfaces. Any key which contains a '.'
                     will be assumed to be a data interface.
        :param date: the datetime of this event
        :param time_spent: a float value representing the duration of the event
        :param event_id: a 32-length unique string identifying this event
        :param extra: a dictionary of additional standard metadata
        :param culprit: a string representing the cause of this event (generally a path to a function)
        :return: a 32-length string identifying this event
        """
        if data is None:
            data = {}
        if extra is None:
            extra = {}
        if not date:
            date = datetime.datetime.utcnow()
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

        for k, v in result.iteritems():
            if k not in data:
                data[k] = v
            else:
                data[k].update(v)

        if stack and 'sentry.interfaces.Stacktrace' not in data:
            if stack is True:
                frames = iter_stack_frames()

            else:
                frames = stack

            data.update({
                'sentry.interfaces.Stacktrace': {
                    'frames': varmap(lambda k, v: shorten(v), get_stack_info(frames))
                },
            })

        if 'sentry.interfaces.Stacktrace' in data and not culprit:
            culprit = get_culprit(data['sentry.interfaces.Stacktrace']['frames'], self.include_paths, self.exclude_paths)

        if not data.get('level'):
            data['level'] = logging.ERROR
        data['modules'] = get_versions(self.include_paths)
        data['server_name'] = self.name
        data.setdefault('extra', {})
        data.setdefault('level', logging.ERROR)

        # Shorten lists/strings
        for k, v in extra.iteritems():
            data['extra'][k] = shorten(v, string_length=self.string_max_length, list_length=self.list_max_length)

        if culprit:
            data['culprit'] = culprit

        if 'checksum' not in data:
            checksum = hashlib.md5()
            for bit in handler.get_hash(data):
                checksum.update(to_unicode(bit) or '')
            data['checksum'] = checksum = checksum.hexdigest()
        else:
            checksum = data['checksum']

        # create ID client-side so that it can be passed to application
        event_id = uuid.uuid4().hex
        data['event_id'] = event_id

        # Run the data through processors
        for processor in self.get_processors():
            data.update(processor.process(data))

        # Make sure all data is coerced
        data = transform(data)

        if 'message' not in data:
            data['message'] = handler.to_string(data)

        data.update({
            'timestamp': date,
            'time_spent': time_spent,
            'event_id': event_id,
        })
        data.setdefault('project', self.project)
        data.setdefault('site', self.site)

        self.send(**data)

        return (event_id, checksum)

    def _send_remote(self, url, data, headers={}):
        parsed = urlparse(url)
        if parsed.scheme == 'udp':
            return self.send_udp(parsed.netloc, data, headers.get('X-Sentry-Auth'))
        return self.send_http(url, data, headers)

    def _get_log_message(self, data):
        # decode message so we can show the actual event
        try:
            data = self.decode(data)
        except:
            message = '<failed decoding data>'
        else:
            message = data.pop('message', '<no message value>')
        return message

    def send_remote(self, url, data, headers={}):
        if not self.state.should_try():
            message = self._get_log_message(data)
            self.error_logger.error(message)
            return

        try:
            self._send_remote(url=url, data=data, headers=headers)
        except Exception, e:
            if isinstance(e, urllib2.HTTPError):
                body = e.read()
                self.error_logger.error('Unable to reach Sentry log server: %s (url: %%s, body: %%s)' % (e,), url, body,
                    exc_info=True, extra={'data': {'body': body, 'remote_url': url}})
            else:
                self.error_logger.error('Unable to reach Sentry log server: %s (url: %%s)' % (e,), url,
                    exc_info=True, extra={'data': {'remote_url': url}})

            message = self._get_log_message(data)
            self.error_logger.error('Failed to submit message: %r', message)
            self.state.set_fail()
        else:
            self.state.set_success()

    def send_udp(self, netloc, data, auth_header):
        if auth_header is None:
            # silently ignore attempts to send messages without an auth header
            return
        host, port = netloc.split(':')
        if self.udp_socket is None:
            self.udp_socket = socket(AF_INET, SOCK_DGRAM)
            self.udp_socket.setblocking(False)
        try:
            self.udp_socket.sendto(auth_header + '\n\n' + data, (host, int(port)))
        except socket_error:
            # as far as I understand things this simply can't happen, but still, it can't hurt
            self.udp_socket.close()
            self.udp_socket = None

    def send_http(self, url, data, headers={}):
        """
        Sends a request to a remote webserver using HTTP POST.
        """
        req = urllib2.Request(url, headers=headers)
        try:
            response = urllib2.urlopen(req, data, self.timeout).read()
        except:
            response = urllib2.urlopen(req, data).read()
        return response

    def send(self, **data):
        """
        Serializes the message and passes the payload onto ``send_encoded``.
        """
        message = self.encode(data)

        return self.send_encoded(message)

    def send_encoded(self, message):
        """
        Given an already serialized message, signs the message and passes the payload
        off to ``send_remote`` for each server specified in the servers configuration.
        """
        for url in self.servers:
            timestamp = time.time()
            signature = get_signature(message, timestamp, self.secret_key or self.key)
            headers = {
                'X-Sentry-Auth': get_auth_header(
                    protocol=self.protocol_version,
                    signature=signature,
                    timestamp=timestamp,
                    client='raven/%s' % (raven.VERSION,),
                    api_key=self.public_key
                ),
                'Content-Type': 'application/octet-stream',
            }

            self.send_remote(url=url, data=message, headers=headers)

    def encode(self, data):
        """
        Serializes ``data`` into a raw string.
        """
        return base64.b64encode(json.dumps(data).encode('zlib'))

    def decode(self, data):
        """
        Unserializes a string, ``data``.
        """
        return json.loads(base64.b64decode(data).decode('zlib'))

    def create_from_text(self, *args, **kwargs):
        warnings.warn("create_from_text is deprecated. Use captureMessage() instead.", DeprecationWarning)
        return self.captureMessage(*args, **kwargs)
    message = create_from_text

    def create_from_exception(self, *args, **kwargs):
        warnings.warn("create_from_exception is deprecated. Use captureException() instead.", DeprecationWarning)
        return self.captureException(*args, **kwargs)
    exception = create_from_exception

    def captureMessage(self, message, **kwargs):
        """
        Creates an event from ``message``.

        >>> client.captureMessage('My event just happened!')
        """
        return self.capture('Message', message=message, **kwargs)

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
        """
        return self.capture('Exception', exc_info=exc_info, **kwargs)

    def captureQuery(self, query, params=(), engine=None, **kwargs):
        """
        Creates an event for a SQL query.

        >>> client.catureQuery('SELECT * FROM foo')
        """
        return self.capture('Query', query=query, params=params, engine=engine, **kwargs)


class DummyClient(Client):
    "Sends messages into an empty void"
    def send(self, **kwargs):
        return None
