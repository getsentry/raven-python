from __future__ import absolute_import


def import_string(key):
    key = str(key)

    if '.' not in key:
        return __import__(key)

    module_name, class_name = key.rsplit('.', 1)
    module = __import__(module_name, {}, {}, [class_name], -1)
    return getattr(module, class_name)
