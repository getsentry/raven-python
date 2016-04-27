from __future__ import absolute_import

import time
import logging
from types import FunctionType

from raven._compat import iteritems, get_code, text_type, string_types
from raven.utils import once


special_logger_handlers = {}


class BreadcrumbBuffer(object):

    def __init__(self, limit=100):
        self.buffer = []
        self.limit = limit

    def record(self, type, data=None, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        self.buffer.append((type, timestamp, data))
        del self.buffer[:-self.limit]

    def clear(self):
        del self.buffer[:]

    def get_buffer(self):
        rv = []
        for type, timestamp, data in self.buffer:
            if data is None:
                data = {}
            elif callable(data):
                data = data()
            rv.append({
                'type': type,
                'data': data,
                'timestamp': timestamp,
            })
        return rv


def record_breadcrumb(type, data=None, timestamp=None):
    """Records a breadcrumb for all active clients.  This is what integration
    code should use rather than invoking the `captureBreadcrumb` method
    on a specific client.  This also additionally permits data to be a
    callable that will be invoked to generate the data if the crumb is not
    discarded.
    """
    if timestamp is None:
        timestamp = time.time()
    for ctx in raven.context.get_active_contexts():
        ctx.breadcrumbs.record(type, data, timestamp)


def _record_log_breadcrumb(logger, level, msg, *args, **kwargs):
    handler = special_logger_handlers.get(logger.name)
    if handler is not None:
        rv = handler(logger, level, msg, args, kwargs)
        if rv:
            return

    def _make_data():
        formatted_msg = text_type(msg)
        if args:
            formatted_msg = msg % args
        return {
            'message': formatted_msg,
            'logger': logger.name,
            'level': logging.getLevelName(level).lower(),
        }
    record_breadcrumb('message', _make_data)


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
    \n''' % {
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
    new_func.__patched_for_raven__ = True

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


@once
def install_logging_hook():
    """Installs the logging hook if it was not installed yet.  Otherwise
    does nothing.
    """
    _patch_logger()


def ignore_logger(name_or_logger):
    """Ignores a logger for the regular breadcrumb code.  This is useful
    for framework integration code where some log messages should be
    specially handled.
    """
    register_special_log_handler(name_or_logger, lambda *args: True)


def register_special_log_handler(name_or_logger, callback):
    """Registers a callback for log handling.  The callback is invoked
    with give arguments: `logger`, `level`, `msg`, `args` and `kwargs`
    which are the values passed to the logging system.  If the callback
    returns `True` the default handling is disabled.
    """
    if isinstance(name_or_logger, string_types):
        name = name_or_logger
    else:
        name = name_or_logger.name
    special_logger_handlers[name] = callback


hooked_libraries = {}


def libraryhook(name):
    def decorator(f):
        f = once(f)
        hooked_libraries[name] = f
        return f
    return decorator


@libraryhook('requests')
def _hook_requests():
    try:
        from requests.sesisons import Session
    except ImportError:
        return

    real_send = Session.send

    def send(self, request, *args, **kwargs):
        def _record_request(response):
            record_breadcrumb('http_request', {
                'url': request.url,
                'method': request.method,
                'status_code': response and response.status or None,
                'reason': response and response.reason or None,
                'classifier': 'requests',
            })
        try:
            resp = real_send(self, request, *args, **kwargs)
        except Exception:
            _record_request(None)
            raise
        else:
            _record_request(resp)
        return resp

    Session.send = send


def hook_libraries(libraries):
    if not libraries:
        libraries = hooked_libraries.keys()
    for lib in libraries:
        func = hooked_libraries.get(lib)
        if func is None:
            raise RuntimeError('Unknown library %r for hooking' % lib)
        func()


import raven.context
