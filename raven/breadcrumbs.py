import time
import logging
from threading import Lock
from datetime import datetime
from types import FunctionType

from raven._compat import iteritems, get_code, text_type


_logging_lock = Lock()
_logging_hooked = False


class BreadcrumbBuffer(object):

    def __init__(self, limit=100):
        self.buffer = []
        self.limit = limit

    def record(self, type, data=None, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        elif isinstance(timestamp, datetime):
            timestamp = datetime

        self.buffer.append({
            'type': type,
            'timestamp': timestamp,
            'data': data or {},
        })
        del self.buffer[:-self.limit]

    def clear(self):
        del self.buffer[:]

    def get_buffer(self):
        return self.buffer[:]


def record_breadcrumb(type, data, timestamp=None):
    if timestamp is None:
        timestamp = time.time()
    for ctx in raven.context.get_active_contexts():
        ctx.breadcrumbs.record(type, data, timestamp)


def _record_log_breadcrumb(logger, level, msg, *args, **kwargs):
    formatted_msg = text_type(msg)
    if args:
        formatted_msg = msg % args
    record_breadcrumb('message', {
        'message': formatted_msg,
        'logger': logger.name,
        'level': logging.getLevelName(level).lower(),
    })


def _wrap_logging_method(meth, level=None):
    if not isinstance(meth, FunctionType):
        func = meth.im_func
    else:
        func = meth

    # We were patched for raven before
    if getattr(func, '__patched_for_raven__', False):
        return

    if level is None:
        args = ('level', 'msg')
        fwd = 'level, msg'
    else:
        args = ('msg',)
        fwd = '%d, msg' % level

    code = get_code(func)

    # This requires a bit of explanation why we're doing this.  Due to how
    # logging itself works we need to pretend that the method actually was
    # created within the logging module.  There are a few ways to detect
    # this and we fake all of them: we use the same function globals (the
    # one from the logging module), we create it entirely there which
    # means that also the filename is set correctly.  This fools the
    # detection code in logging and it makes logging itself skip past our
    # code when determining the code location.
    #
    # Because we point the globals to the logging module we now need to
    # refer to our own functions (original and the crumb recording
    # function) through a closure instead of the global scope.
    #
    # We also add a lot of newlines in front of the code so that the
    # code location lines up again in case someone runs inspect.getsource
    # on the function.
    ns = {}
    eval(compile('''%(offset)sif 1:
    def factory(original, record_crumb):
        def %(name)s(self, %(args)s, *args, **kwargs):
            record_crumb(self, %(fwd)s, *args, **kwargs)
            return original(self, %(args)s, *args, **kwargs)
        return %(name)s
    ''' % {
        'offset': '\n' * (code.co_firstlineno - 3),
        'name': func.__name__,
        'args': ', '.join(args),
        'fwd': fwd,
        'level': level,
    }, logging.__file__, 'exec'), logging.__dict__, ns)

    new_func = ns['factory'](meth, _record_log_breadcrumb)
    new_func.__doc__ = func.__doc__

    assert code.co_firstlineno == get_code(func).co_firstlineno
    assert new_func.__module__ == func.__module__
    assert new_func.__name__ == func.__name__

    return new_func


def _patch_logger():
    cls = logging.Logger

    methods = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'warn': logging.WARN,
        'error': logging.ERROR,
        'exception': logging.ERROR,
        'critical': logging.CRITICAL,
        'fatal': logging.FATAL
    }

    for method_name, level in iteritems(methods):
        new_func = _wrap_logging_method(
            getattr(cls, method_name), level)
        setattr(logging.Logger, method_name, new_func)

    logging.Logger.log = _wrap_logging_method(
        logging.Logger.log)


def install_logging_hook():
    global _logging_hooked
    if _logging_hooked:
        return
    with _logging_lock:
        if _logging_hooked:
            return
        _patch_logger()
        _logging_hooked = True


import raven.context
