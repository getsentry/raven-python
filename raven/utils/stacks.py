"""
raven.utils.stacks
~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import inspect
import re
import sys
import warnings

from raven.utils.serializer import transform

_coding_re = re.compile(r'coding[:=]\s*([-\w.]+)')


def get_lines_from_file(filename, lineno, context_lines, loader=None, module_name=None):
    """
    Returns context_lines before and after lineno from file.
    Returns (pre_context_lineno, pre_context, context_line, post_context).
    """
    source = None
    if loader is not None and hasattr(loader, "get_source"):
        try:
            source = loader.get_source(module_name)
        except ImportError:
            # Traceback (most recent call last):
            #   File "/Users/dcramer/Development/django-sentry/sentry/client/handlers.py", line 31, in emit
            #     get_client().create_from_record(record, request=request)
            #   File "/Users/dcramer/Development/django-sentry/sentry/client/base.py", line 325, in create_from_record
            #     data['__sentry__']['frames'] = varmap(shorten, get_stack_info(stack))
            #   File "/Users/dcramer/Development/django-sentry/sentry/utils/stacks.py", line 112, in get_stack_info
            #     pre_context_lineno, pre_context, context_line, post_context = get_lines_from_file(filename, lineno, 7, loader, module_name)
            #   File "/Users/dcramer/Development/django-sentry/sentry/utils/stacks.py", line 24, in get_lines_from_file
            #     source = loader.get_source(module_name)
            #   File "/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/pkgutil.py", line 287, in get_source
            #     fullname = self._fix_name(fullname)
            #   File "/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/pkgutil.py", line 262, in _fix_name
            #     "module %s" % (self.fullname, fullname))
            # ImportError: Loader for module cProfile cannot handle module __main__
            source = None
        if source is not None:
            source = source.splitlines()
    if source is None:
        try:
            f = open(filename)
            try:
                source = f.readlines()
            finally:
                f.close()
        except (OSError, IOError):
            pass
    if source is None:
        return None, [], None

    encoding = 'ascii'
    for line in source[:2]:
        # File coding may be specified. Match pattern from PEP-263
        # (http://www.python.org/dev/peps/pep-0263/)
        match = _coding_re.search(line)
        if match:
            encoding = match.group(1)
            break
    source = [unicode(sline, encoding, 'replace') for sline in source]

    lower_bound = max(0, lineno - context_lines)
    upper_bound = min(lineno + 1 + context_lines, len(source))

    try:
        pre_context = [line.strip('\n') for line in source[lower_bound:lineno]]
        context_line = source[lineno].strip('\n')
        post_context = [line.strip('\n') for line in source[(lineno + 1):upper_bound]]
    except IndexError:
        # the file may have changed since it was loaded into memory
        return None, [], None

    return pre_context, context_line, post_context


def get_culprit(frames, *args, **kwargs):
    # We iterate through each frame looking for a deterministic culprit
    # When one is found, we mark it as last "best guess" (best_guess) and then
    # check it against ``exclude_paths``. If it isnt listed, then we
    # use this option. If nothing is found, we use the "best guess".
    if args or kwargs:
        warnings.warn('get_culprit no longer does application detection')

    best_guess = None
    culprit = None
    for frame in reversed(frames):
        try:
            culprit = '%s in %s' % (frame.get('module') or '<unknown module>',
                frame.get('function') or '<unknown function>')
        except KeyError:
            continue

        if frame.get('in_app'):
            return culprit
        elif not best_guess:
            best_guess = culprit
        elif best_guess:
            break

    # Return either the best guess or the last frames call
    return best_guess or culprit


def _getitem_from_frame(f_locals, key, default=None):
    """
    f_locals is not guaranteed to have .get(), but it will always
    support __getitem__. Even if it doesnt, we return ``default``.
    """
    try:
        return f_locals[key]
    except Exception:
        return default


def to_dict(dictish):
    """
    Given something that closely resembles a dictionary, we attempt
    to coerce it into a propery dictionary.
    """
    if hasattr(dictish, 'iterkeys'):
        m = dictish.iterkeys
    elif hasattr(dictish, 'keys'):
        m = dictish.keys
    else:
        raise ValueError(dictish)

    return dict((k, dictish[k]) for k in m())


def iter_traceback_frames(tb):
    """
    Given a traceback object, it will iterate over all
    frames that do not contain the ``__traceback_hide__``
    local variable.
    """
    while tb:
        # support for __traceback_hide__ which is used by a few libraries
        # to hide internal frames.
        f_locals = getattr(tb.tb_frame, 'f_locals', {})
        if not _getitem_from_frame(f_locals, '__traceback_hide__'):
            yield tb.tb_frame, getattr(tb, 'tb_lineno', None)
        tb = tb.tb_next


def iter_stack_frames(frames=None):
    """
    Given an optional list of frames (defaults to current stack),
    iterates over all frames that do not contain the ``__traceback_hide__``
    local variable.
    """
    if not frames:
        frames = inspect.stack()[1:]

    for frame, lineno in ((f[0], f[2]) for f in frames):
        f_locals = getattr(frame, 'f_locals', {})
        if _getitem_from_frame(f_locals, '__traceback_hide__'):
            continue
        yield frame, lineno


def get_stack_info(frames, list_max_length=None, string_max_length=None):
    """
    Given a list of frames, returns a list of stack information
    dictionary objects that are JSON-ready.

    We have to be careful here as certain implementations of the
    _Frame class do not contain the nescesary data to lookup all
    of the information we want.
    """
    __traceback_hide__ = True  # NOQA

    results = []
    for frame_info in frames:
        # Old, terrible API
        if isinstance(frame_info, (list, tuple)):
            frame, lineno = frame_info

        else:
            frame = frame_info
            lineno = frame_info.f_lineno

        # Support hidden frames
        f_locals = getattr(frame, 'f_locals', {})
        if _getitem_from_frame(f_locals, '__traceback_hide__'):
            continue

        f_globals = getattr(frame, 'f_globals', {})

        f_code = getattr(frame, 'f_code', None)
        if f_code:
            abs_path = frame.f_code.co_filename
            function = frame.f_code.co_name
        else:
            abs_path = None
            function = None

        loader = _getitem_from_frame(f_globals, '__loader__')
        module_name = _getitem_from_frame(f_globals, '__name__')

        if lineno:
            lineno -= 1

        if lineno is not None and abs_path:
            pre_context, context_line, post_context = get_lines_from_file(abs_path, lineno, 5, loader, module_name)
        else:
            pre_context, context_line, post_context = [], None, []

        # Try to pull a relative file path
        # This changes /foo/site-packages/baz/bar.py into baz/bar.py
        try:
            base_filename = sys.modules[module_name.split('.', 1)[0]].__file__
            filename = abs_path.split(base_filename.rsplit('/', 2)[0], 1)[-1][1:]
        except:
            filename = abs_path

        if not filename:
            filename = abs_path

        if f_locals is not None and not isinstance(f_locals, dict):
            # XXX: Genshi (and maybe others) have broken implementations of
            # f_locals that are not actually dictionaries
            try:
                f_locals = to_dict(f_locals)
            except Exception:
                f_locals = '<invalid local scope>'

        frame_result = {
            'abs_path': abs_path,
            'filename': filename,
            'module': module_name or None,
            'function': function or '<unknown>',
            'lineno': lineno + 1,
            'vars': transform(f_locals, list_max_length=list_max_length,
                string_max_length=string_max_length),
        }
        if context_line:
            frame_result.update({
                'pre_context': pre_context,
                'context_line': context_line,
                'post_context': post_context,
            })

        results.append(frame_result)
    return results
