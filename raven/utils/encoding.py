"""
raven.utils.encoding
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import uuid
from types import ClassType, TypeType


def force_unicode(s, encoding='utf-8', errors='strict'):
    """
    Similar to smart_unicode, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    Adapted from Django
    """
    try:
        if not isinstance(s, basestring,):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                try:
                    s = unicode(str(s), encoding, errors)
                except UnicodeEncodeError:
                    if not isinstance(s, Exception):
                        raise
                    # If we get to here, the caller has passed in an Exception
                    # subclass populated with non-ASCII data without special
                    # handling to display as a string. We need to handle this
                    # without raising a further exception. We do an
                    # approximation to what the Exception's standard str()
                    # output should be.
                    s = ' '.join([force_unicode(arg, encoding,
                            errors) for arg in s])
        elif not isinstance(s, unicode):
            # Note: We use .decode() here, instead of unicode(s, encoding,
            # errors), so that if s is a SafeString, it ends up being a
            # SafeUnicode at the end.
            s = s.decode(encoding, errors)
    except UnicodeDecodeError, e:
        if not isinstance(s, Exception):
            raise UnicodeDecodeError(s, *e.args)
        else:
            # If we get to here, the caller has passed in an Exception
            # subclass populated with non-ASCII bytestring data without a
            # working unicode method. Try to handle this without raising a
            # further exception by individually forcing the exception args
            # to unicode.
            s = ' '.join([force_unicode(arg, encoding,
                    errors) for arg in s])
    return s


def _has_sentry_metadata(value):
    try:
        return callable(value.__getattribute__("__sentry__"))
    except:
        return False


def transform(value, stack=[], context=None):
    # TODO: make this extendable
    if context is None:
        context = {}

    objid = id(value)
    if objid in context:
        return '<...>'

    context[objid] = 1
    transform_rec = lambda o: transform(o, stack + [value], context)

    if any(value is s for s in stack):
        ret = 'cycle'
    elif isinstance(value, (tuple, list, set, frozenset)):
        try:
            ret = type(value)(transform_rec(o) for o in value)
        except Exception:
            # We may be dealing with a namedtuple
            class value_type(list):
                __name__ = type(value).__name__
            ret = value_type(transform_rec(o) for o in value[:])
    elif isinstance(value, uuid.UUID):
        ret = repr(value)
    elif isinstance(value, dict):
        ret = dict((to_string(k), transform_rec(v)) for k, v in value.iteritems())
    elif isinstance(value, unicode):
        ret = to_unicode(value)
    elif isinstance(value, str):
        ret = to_string(value)
    elif not isinstance(value, (ClassType, TypeType)) and \
            _has_sentry_metadata(value):
        ret = transform_rec(value.__sentry__())
    # elif isinstance(value, Promise):
    #     # EPIC HACK
    #     # handles lazy model instances (which are proxy values that dont easily give you the actual function)
    #     pre = value.__class__.__name__[1:]
    #     value = getattr(value, '%s__func' % pre)(*getattr(value, '%s__args' % pre), **getattr(value, '%s__kw' % pre))
    #     return transform(value)
    elif isinstance(value, bool):
        ret = bool(value)
    elif isinstance(value, float):
        ret = float(value)
    elif isinstance(value, int):
        ret = int(value)
    elif value is not None:
        try:
            ret = transform(repr(value))
        except:
            # It's common case that a model's __unicode__ definition may try to query the database
            # which if it was not cleaned up correctly, would hit a transaction aborted exception
            ret = u'<BadRepr: %s>' % type(value)
    else:
        ret = None
    del context[objid]
    return ret


def to_unicode(value):
    try:
        value = unicode(force_unicode(value))
    except (UnicodeEncodeError, UnicodeDecodeError):
        value = '(Error decoding value)'
    except Exception:  # in some cases we get a different exception
        try:
            value = str(repr(type(value)))
        except Exception:
            value = '(Error decoding value)'
    return value


def to_string(value):
    try:
        return str(value.decode('utf-8').encode('utf-8'))
    except:
        return to_unicode(value).encode('utf-8')


def shorten(var, list_length=50, string_length=200):
    var = transform(var)
    if isinstance(var, basestring) and len(var) > string_length:
        var = var[:string_length] + '...'
    elif isinstance(var, (list, tuple, set, frozenset)) and len(var) > list_length:
        # TODO: we should write a real API for storing some metadata with vars when
        # we get around to doing ref storage
        # TODO: when we finish the above, we should also implement this for dicts
        var = list(var)[:list_length] + ['...', '(%d more elements)' % (len(var) - list_length,)]
    return var
