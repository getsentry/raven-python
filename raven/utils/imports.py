from __future__ import absolute_import

from . import six


def import_string(key):
    # HACK(dcramer): Ensure a unicode key is still importable
    if not six.PY3:
        key = str(key)

    if '.' not in key:
        return __import__(key)

    module_name, class_name = key.rsplit('.', 1)
    module = __import__(module_name, {}, {}, [class_name], 0)
    return getattr(module, class_name)
