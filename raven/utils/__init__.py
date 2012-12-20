"""
raven.utils
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import logging
try:
    import pkg_resources
except ImportError:
    pkg_resources = None  # NOQA
import sys

logger = logging.getLogger('raven.errors')


def varmap(func, var, context=None, name=None):
    """
    Executes ``func(key_name, value)`` on all values
    recurisively discovering dict and list scoped
    values.
    """
    if context is None:
        context = {}
    objid = id(var)
    if objid in context:
        return func(name, '<...>')
    context[objid] = 1
    if isinstance(var, dict):
        ret = dict((k, varmap(func, v, context, k)) for k, v in var.iteritems())
    elif isinstance(var, (list, tuple)):
        ret = [varmap(func, f, context, name) for f in var]
    else:
        ret = func(name, var)
    del context[objid]
    return ret

# We store a cache of module_name->version string to avoid
# continuous imports and lookups of modules
_VERSION_CACHE = {}


def get_version_from_app(module_name, app):
    if hasattr(app, 'get_version'):
        get_version = app.get_version
        if callable(get_version):
            version = get_version()
        else:
            version = get_version
    elif hasattr(app, 'VERSION'):
        version = app.VERSION
    elif hasattr(app, '__version__'):
        version = app.__version__
    elif pkg_resources:
        # pull version from pkg_resources if distro exists
        try:
            version = pkg_resources.get_distribution(module_name).version
        except pkg_resources.DistributionNotFound:
            return None
    else:
        return None

    if isinstance(version, (list, tuple)):
        version = '.'.join(str(o) for o in version)

    return version


def get_versions(module_list=None):
    if not module_list:
        return {}

    ext_module_list = set()
    for m in module_list:
        parts = m.split('.')
        ext_module_list.update('.'.join(parts[:idx]) for idx in xrange(1, len(parts) + 1))

    versions = {}
    for module_name in ext_module_list:
        if module_name not in _VERSION_CACHE:
            try:
                __import__(module_name)
            except ImportError:
                continue

            try:
                app = sys.modules[module_name]
            except KeyError:
                continue

            try:
                version = get_version_from_app(module_name, app)
            except Exception, e:
                logger.exception(e)
                version = None

            _VERSION_CACHE[module_name] = version
        else:
            version = _VERSION_CACHE[module_name]
        if version is None:
            continue
        versions[module_name] = version
    return versions


def get_auth_header(protocol, timestamp, client, api_key, api_secret=None, **kwargs):
    header = [
        ('sentry_timestamp', timestamp),
        ('sentry_client', client),
        ('sentry_version', protocol),
        ('sentry_key', api_key),
    ]
    if api_secret:
        header.append(('sentry_secret', api_secret))

    return 'Sentry %s' % ', '.join('%s=%s' % (k, v) for k, v in header)
