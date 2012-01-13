"""
raven.base
~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import base64
import datetime
import logging
import sys
import time
import traceback
import urllib2
import uuid

import raven
from raven.conf import defaults
from raven.utils import json, construct_checksum, varmap, \
                                get_versions, get_signature, get_auth_header
from raven.utils.encoding import transform, force_unicode, shorten
from raven.utils.stacks import get_stack_info, iter_stack_frames, iter_traceback_frames, \
                                       get_culprit

logger = logging.getLogger('sentry.errors.client')

class Client(object):
    """
    The base Raven client, which handles both local direct communication with Sentry (through
    the GroupedMessage API), as well as communicating over the HTTP API to multiple servers.

    >>> from raven import Client
    >>>
    >>> client = Client(servers=['http://sentry.local/store/'], include_paths=['my.package'])
    >>> try:
    >>>     1/0
    >>> except ZeroDivisionError:
    >>>     ident = client.get_ident(client.create_from_exception())
    >>>     print "Exception caught; reference is %%s" %% ident
    """

    def __init__(self, servers, include_paths=None, exclude_paths=None, timeout=None,
                 name=None, auto_log_stacks=None, key=None, string_max_length=None,
                 list_max_length=None, site=None, **kwargs):
        # servers may be set to a NoneType (for Django)
        if servers and not key:
            raise TypeError('You must specify a key to communicate with the remote Sentry servers.')

        self.servers = servers
        self.include_paths = include_paths or set(defaults.INCLUDE_PATHS)
        self.exclude_paths = exclude_paths or set(defaults.EXCLUDE_PATHS)
        self.timeout = timeout or int(defaults.TIMEOUT)
        self.name = name or unicode(defaults.NAME)
        self.auto_log_stacks = auto_log_stacks or bool(defaults.AUTO_LOG_STACKS)
        self.key = key or defaults.KEY
        self.string_max_length = string_max_length or int(defaults.MAX_LENGTH_STRING)
        self.list_max_length = list_max_length or int(defaults.MAX_LENGTH_LIST)
        self.site = site or unicode(defaults.SITE)

    def get_ident(self, result):
        """
        Returns a searchable string representing a message.

        >>> result = client.process(**kwargs)
        >>> ident = client.get_ident(result)
        """
        return '$'.join(result)

    def process(self, **kwargs):
        """
        Processes the message before passing it on to the server.

        This includes:

        - extracting stack frames (for non exceptions)
        - identifying module versions
        - coercing data
        - generating message identifiers

        You may pass the ``stack`` parameter to specify an explicit stack,
        or simply to tell Raven that you want to capture the stacktrace.

        To automatically grab the stack from a non-exception:

        >>> client.process(message='test', stack=True)

        To capture an explicit stack (e.g. something from a different threadframe?):

        >>> import inspect
        >>> from raven.utils import iter_stack_frames
        >>> client.process(message='test', stack=iter_stack_frames(inspect.stack()))

        """

        if kwargs.get('data'):
            # Ensure we're not changing the original data which was passed
            # to Sentry
            data = kwargs.get('data').copy()
        else:
            data = {}

        if '__sentry__' not in data:
            data['__sentry__'] = {}

        get_stack = kwargs.pop('stack', self.auto_log_stacks)
        if get_stack and not data['__sentry__'].get('frames'):
            if get_stack is True:
                stack = []
                found = None
                for frame in iter_stack_frames():
                    # There are initial frames from Sentry that need skipped
                    name = frame.f_globals.get('__name__')
                    if found is None:
                        if name == 'logging':
                            found = False
                        continue
                    elif not found:
                        if name != 'logging':
                            found = True
                        else:
                            continue
                    stack.append(frame)
            else:
                # assume stack was a list of frames
                stack = get_stack or []
            data['__sentry__']['frames'] = varmap(shorten, get_stack_info(stack))

        kwargs.setdefault('level', logging.ERROR)
        kwargs.setdefault('server_name', self.name)
        kwargs.setdefault('site', self.site)

        versions = get_versions(self.include_paths)
        data['__sentry__']['versions'] = versions

        # Shorten lists/strings
        for k, v in data.iteritems():
            if k == '__sentry__':
                continue
            data[k] = shorten(v, string_length=self.string_max_length, list_length=self.list_max_length)

        # if we've passed frames, lets try to fetch the culprit
        if not kwargs.get('view') and data['__sentry__'].get('frames'):
            # We iterate through each frame looking for an app in INSTALLED_APPS
            # When one is found, we mark it as last "best guess" (best_guess) and then
            # check it against SENTRY_EXCLUDE_PATHS. If it isnt listed, then we
            # use this option. If nothing is found, we use the "best guess".
            view = get_culprit(data['__sentry__']['frames'], self.include_paths, self.exclude_paths)

            if view:
                kwargs['view'] = view

        # try to fetch the current version
        if kwargs.get('view'):
            # get list of modules from right to left
            parts = kwargs['view'].split('.')
            module_list = ['.'.join(parts[:idx]) for idx in xrange(1, len(parts) + 1)][::-1]
            version = None
            module = None
            for m in module_list:
                if m in versions:
                    module = m
                    version = versions[m]

            # store our "best guess" for application version
            if version:
                data['__sentry__'].update({
                    'version': version,
                    'module': module,
                })

        if 'checksum' not in kwargs:
            kwargs['checksum'] = checksum = construct_checksum(**kwargs)
        else:
            checksum = kwargs['checksum']

        # create ID client-side so that it can be passed to application
        message_id = uuid.uuid4().hex
        kwargs['message_id'] = message_id

        # Make sure all data is coerced
        kwargs['data'] = transform(data)

        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.datetime.now()

        self.send(**kwargs)

        return (message_id, checksum)

    def send_remote(self, url, data, headers={}):
        """
        Sends a request to a remote webserver using HTTP POST.
        """
        req = urllib2.Request(url, headers=headers)
        try:
            response = urllib2.urlopen(req, data, self.timeout).read()
        except:
            response = urllib2.urlopen(req, data).read()
        return response

    def send(self, **kwargs):
        """
        Sends the message to the server.

        If ``servers`` was passed into the constructor, this will serialize the data and pipe it to
        each server using ``send_remote()``. Otherwise, this will communicate with ``sentry.models.GroupedMessage``
        directly.
        """
        message = base64.b64encode(json.dumps(kwargs).encode('zlib'))
        for url in self.servers:
            timestamp = time.time()
            signature = get_signature(self.key, message, timestamp)
            headers = {
                'Authorization': get_auth_header(signature, timestamp, '%s/%s' % (self.__class__.__name__, raven.VERSION)),
                'Content-Type': 'application/octet-stream',
            }

            try:
                self.send_remote(url=url, data=message, headers=headers)
            except urllib2.HTTPError, e:
                body = e.read()
                logger.error('Unable to reach Sentry log server: %s (url: %%s, body: %%s)' % (e,), url, body,
                             exc_info=True, extra={'data': {'body': body, 'remote_url': url}})
                logger.log(kwargs.pop('level', None) or logging.ERROR, kwargs.pop('message', None))
            except urllib2.URLError, e:
                logger.error('Unable to reach Sentry log server: %s (url: %%s)' % (e,), url,
                             exc_info=True, extra={'data': {'remote_url': url}})
                logger.log(kwargs.pop('level', None) or logging.ERROR, kwargs.pop('message', None))

    def create_from_record(self, record, **kwargs):
        """
        Creates an event for a ``logging`` module ``record`` instance.

        If the record contains an attribute, ``stack``, that evaluates to True,
        it will pass this information on to process in order to grab the stack
        frames.

        >>> class ExampleHandler(logging.Handler):
        >>>     def emit(self, record):
        >>>         self.format(record)
        >>>         client.create_from_record(record)
        """
        for k in ('url', 'view', 'data'):
            if not kwargs.get(k):
                kwargs[k] = record.__dict__.get(k)

        kwargs.update({
            'logger': record.name,
            'level': record.levelno,
            'message': force_unicode(record.msg),
            'server_name': self.name,
            'stack': getattr(record, 'stack', self.auto_log_stacks),
        })

        # construct the checksum with the unparsed message
        kwargs['checksum'] = construct_checksum(**kwargs)

        # save the message with included formatting
        kwargs['message'] = record.getMessage()

        # If there's no exception being processed, exc_info may be a 3-tuple of None
        # http://docs.python.org/library/sys.html#sys.exc_info
        if record.exc_info and all(record.exc_info):
            return self.create_from_exception(record.exc_info, **kwargs)

        return self.process(
            traceback=record.exc_text,
            **kwargs
        )

    def create_from_text(self, message, **kwargs):
        """
        Creates an event for from ``message``.

        >>> client.create_from_text('My event just happened!')
        """
        return self.process(
            message=message,
            **kwargs
        )

    def create_from_exception(self, exc_info=None, **kwargs):
        """
        Creates an event from an exception.

        >>> try:
        >>>     exc_info = sys.exc_info()
        >>>     client.create_from_exception(exc_info)
        >>> finally:
        >>>     del exc_info
        """
        new_exc = bool(exc_info)
        if not exc_info or exc_info is True:
            exc_info = sys.exc_info()

        data = kwargs.pop('data', {}) or {}

        try:
            exc_type, exc_value, exc_traceback = exc_info

            frames = varmap(shorten, get_stack_info(iter_traceback_frames(exc_traceback)))

            if hasattr(exc_type, '__class__'):
                exc_module = exc_type.__class__.__module__
            else:
                exc_module = None

            data['__sentry__'] = {}
            data['__sentry__']['frames'] = frames
            data['__sentry__']['exception'] = [exc_module, exc_value.args]

            tb_message = '\n'.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

            kwargs.setdefault('message', transform(force_unicode(exc_value)))

            return self.process(
                class_name=exc_type.__name__,
                traceback=tb_message,
                data=data,
                **kwargs
            )
        finally:
            if new_exc:
                try:
                    del exc_info
                except Exception, e:
                    logger.exception(e)

class DummyClient(Client):
    "Sends messages into an empty void"
    def send(self, **kwargs):
        return None
