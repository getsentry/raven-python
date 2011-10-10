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
    def __init__(self, *args, **kwargs):
        self.include_paths = kwargs.get('include_paths') or defaults.INCLUDE_PATHS
        self.exclude_paths = kwargs.get('exclude_paths') or defaults.EXCLUDE_PATHS
        self.timeout = kwargs.get('timeout') or defaults.TIMEOUT
        self.servers = kwargs.get('servers') or defaults.SERVERS
        self.name = kwargs.get('name') or defaults.NAME
        self.auto_log_stacks = kwargs.get('auto_log_stacks') or defaults.AUTO_LOG_STACKS
        self.key = kwargs.get('key') or defaults.KEY
        self.string_max_length = kwargs.get('string_max_length') or defaults.MAX_LENGTH_STRING
        self.list_max_length = kwargs.get('list_max_length') or defaults.MAX_LENGTH_LIST

    def process(self, **kwargs):
        "Processes the message before passing it on to the server"
        if kwargs.get('data'):
            # Ensure we're not changing the original data which was passed
            # to Sentry
            kwargs['data'] = kwargs['data'].copy()
        else:
            kwargs['data'] = {}

        if '__sentry__' not in kwargs['data']:
            kwargs['data']['__sentry__'] = {}

        kwargs.setdefault('level', logging.ERROR)
        kwargs.setdefault('server_name', self.name)

        versions = get_versions(self.include_paths)
        kwargs['data']['__sentry__']['versions'] = versions

        # Shorten lists/strings
        for k, v in kwargs['data'].iteritems():
            if k == '__sentry__':
                continue
            kwargs['data'][k] = shorten(v, string_length=self.string_max_length, list_length=self.list_max_length)

        # if we've passed frames, lets try to fetch the culprit
        if not kwargs.get('view') and kwargs['data']['__sentry__'].get('frames'):
            # We iterate through each frame looking for an app in INSTALLED_APPS
            # When one is found, we mark it as last "best guess" (best_guess) and then
            # check it against SENTRY_EXCLUDE_PATHS. If it isnt listed, then we
            # use this option. If nothing is found, we use the "best guess".
            view = get_culprit(kwargs['data']['__sentry__']['frames'], self.include_paths, self.exclude_paths)

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
                kwargs['data']['__sentry__'].update({
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
        kwargs['data'] = transform(kwargs['data'])

        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.datetime.now()

        self.send(**kwargs)

        return (message_id, checksum)

    def send_remote(self, url, data, headers={}):
        req = urllib2.Request(url, headers=headers)
        try:
            response = urllib2.urlopen(req, data, self.timeout).read()
        except:
            response = urllib2.urlopen(req, data).read()
        return response

    def send(self, **kwargs):
        "Sends the message to the server."
        if self.servers:
            message = base64.b64encode(json.dumps(kwargs).encode('zlib'))
            for url in self.servers:
                timestamp = time.time()
                signature = get_signature(self.key, message, timestamp)
                headers = {
                    'Authorization': get_auth_header(signature, timestamp, '%s/%s' % (self.__class__.__name__, raven.VERSION)),
                    'Content-Type': 'application/octet-stream',
                }

                try:
                    return self.send_remote(url=url, data=message, headers=headers)
                except urllib2.HTTPError, e:
                    body = e.read()
                    logger.error('Unable to reach Sentry log server: %s (url: %%s, body: %%s)' % (e,), url, body,
                                 exc_info=True, extra={'data': {'body': body, 'remote_url': url}})
                    logger.log(kwargs.pop('level', None) or logging.ERROR, kwargs.pop('message', None))
                except urllib2.URLError, e:
                    logger.error('Unable to reach Sentry log server: %s (url: %%s)' % (e,), url,
                                 exc_info=True, extra={'data': {'remote_url': url}})
                    logger.log(kwargs.pop('level', None) or logging.ERROR, kwargs.pop('message', None))
        else:
            from sentry.models import GroupedMessage

            return GroupedMessage.objects.from_kwargs(**kwargs)

    def create_from_record(self, record, **kwargs):
        """
        Creates an error log for a ``logging`` module ``record`` instance.
        """
        for k in ('url', 'view', 'data'):
            if not kwargs.get(k):
                kwargs[k] = record.__dict__.get(k)

        kwargs.update({
            'logger': record.name,
            'level': record.levelno,
            'message': force_unicode(record.msg),
            'server_name': self.name,
        })

        # construct the checksum with the unparsed message
        kwargs['checksum'] = construct_checksum(**kwargs)

        # save the message with included formatting
        kwargs['message'] = record.getMessage()

        # If there's no exception being processed, exc_info may be a 3-tuple of None
        # http://docs.python.org/library/sys.html#sys.exc_info
        if record.exc_info and all(record.exc_info):
            return self.create_from_exception(record.exc_info, **kwargs)

        data = kwargs.pop('data', {}) or {}
        data['__sentry__'] = {}
        if getattr(record, 'stack', self.auto_log_stacks):
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
            data['__sentry__']['frames'] = varmap(shorten, get_stack_info(stack))

        return self.process(
            traceback=record.exc_text,
            data=data,
            **kwargs
        )

    def create_from_text(self, message, **kwargs):
        """
        Creates an error log for from ``message``.
        """
        return self.process(
            message=message,
            **kwargs
        )

    def create_from_exception(self, exc_info=None, **kwargs):
        """
        Creates an error log from an exception.
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
