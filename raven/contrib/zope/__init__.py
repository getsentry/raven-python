#!/usr/bin/python
# -*- coding: utf-8 -*-

from inspect import getouterframes, currentframe, getinnerframes
from raven.handlers.logging import SentryHandler
from ZConfig.components.logger.factory import Factory
import logging

from raven.utils.stacks import iter_stack_frames


class ZopeSentryHandlerFactory(Factory):

    def getLevel(self):
        return self.section.level

    def create(self):
        return ZopeSentryHandler(**self.section.__dict__)

    def __init__(self, section):
        Factory.__init__(self)
        self.section = section


class ZopeSentryHandler(SentryHandler):
    """
    Zope unfortunately eats the stack trace information.
    To get the stack trace information and other useful information
    from the request object, this class looks into the different stack
    frames when the emit method is invoked.
    """

    def __init__(self, *args, **kw):
        super(ZopeSentryHandler, self).__init__(*args, **kw)
        level = kw.get('level', logging.ERROR)
        self.setLevel(level)

    def emit(self, record):
        if record.levelno <= logging.ERROR:
            request = None
            exc_info = None
            for frame_info in getouterframes(currentframe()):
                frame = frame_info[0]
                request = frame.f_locals.get('request', None)
                exc_info = frame.f_locals.get('exc_info', None)
                if request and exc_info:
                    break
            if exc_info:
                record.exc_info = exc_info
                record.stack = \
                    iter_stack_frames(getinnerframes(exc_info[2]))
            if request:
                try:
                    body_pos = request.stdin.tell()
                    request.stdin.seek(0)
                    body = request.stdin.read()
                    request.stdin.seek(body_pos)
                    data = dict(headers=request.environ,
                                url=request.getURL(),
                                method=request.method,
                                host=request.environ.get('REMOTE_ADDR',
                                ''), data=body)
                    if not hasattr(record, 'data'):
                        record.data = {}
                    record.data['sentry.interfaces.Http'] = data
                    user = request.AUTHENTICATED_USER
                    user_dict = dict(id=user.getId(),
                            is_authenticated=user.has_role('Authenticated'
                            ), email='todo')
                    record.data['sentry.interfaces.User'] = user_dict
                except (AttributeError, KeyError):
                    pass
        return super(ZopeSentryHandler, self).emit(record)
