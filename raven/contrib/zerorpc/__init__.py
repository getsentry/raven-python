"""
raven.contrib.zerorpc
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import inspect

from raven.base import Client
from raven.utils.stacks import iter_traceback_frames


class SentryMiddleware(object):
    """Sentry/Raven middleware for ZeroRPC.

    >>> sentry = SentryMiddleware(dsn='udp://..../')
    >>> zerorpc.Context.get_instance().register_middleware(sentry)

    Exceptions detected server-side in ZeroRPC will be submitted to Sentry (and
    propagated to the client as well).

    hide_zerorpc_frames: modify the exception stacktrace to remove the internal
                         zerorpc frames (True by default to make the stacktrace
                         as readable as possible);
    client: use an existing raven.Client object, otherwise one will be
            instantiated from the keyword arguments.

    """

    def __init__(self, hide_zerorpc_frames=True, client=None, **kwargs):
        self._sentry_client = client or Client(**kwargs)
        self._hide_zerorpc_frames = hide_zerorpc_frames

    def inspect_error(self, task_context, exc_info):
        """Called when an exception has been raised in the code run by ZeroRPC"""

        # Hide the zerorpc internal frames for readability, frames to hide are:
        # - core.ServerBase._async_task
        # - core.Pattern*.process_call
        # - context.Context.middleware_call_procedure
        # - core.DecoratorBase.__call__
        if self._hide_zerorpc_frames:
            exc_traceback = exc_info[2]
            for zerorpc_frame, tb_lineno in iter_traceback_frames(exc_traceback):
                zerorpc_frame.f_locals['__traceback_hide__'] = True
                frame_info = inspect.getframeinfo(zerorpc_frame)
                # Is there a better way than this (or looking up the filenames or
                # hardcoding the number of frames to skip) to know when we are out
                # of zerorpc?
                if frame_info.function == '__call__':
                    break

        self._sentry_client.captureException(
            exc_info,
            extra=task_context
        )
