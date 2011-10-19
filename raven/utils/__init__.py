"""
raven.utils
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import hashlib
import hmac
import logging
try:
    import pkg_resources
except ImportError:
    pkg_resources = None
import sys

import raven

def construct_checksum(level=logging.ERROR, class_name='', traceback='', message='', **kwargs):
    checksum = hashlib.md5(str(level))
    checksum.update(class_name or '')

    if 'data' in kwargs and kwargs['data'] and '__sentry__' in kwargs['data'] and 'frames' in kwargs['data']['__sentry__']:
        frames = kwargs['data']['__sentry__']['frames']
        for frame in frames:
            checksum.update(frame['module'] or '<no module>')
            checksum.update(frame['function'] or '<no function>')

    elif traceback:
        traceback = '\n'.join(traceback.split('\n')[:-3])

    elif message:
        if isinstance(message, unicode):
            message = message.encode('utf-8', 'replace')
        checksum.update(message)

    return checksum.hexdigest()

def varmap(func, var, context=None):
    if context is None:
        context = {}
    objid = id(var)
    if objid in context:
        return func('<...>')
    context[objid] = 1
    if isinstance(var, dict):
        ret = dict((k, varmap(func, v, context)) for k, v in var.iteritems())
    elif isinstance(var, (list, tuple)):
        ret = [varmap(func, f, context) for f in var]
    else:
        ret = func(var)
    del context[objid]
    return ret

# We store a cache of module_name->version string to avoid
# continuous imports and lookups of modules
_VERSION_CACHE = {}
def get_versions(module_list=None):
    if not module_list:
        return {}

    ext_module_list = set()
    for m in module_list:
        parts = m.split('.')
        ext_module_list.update('.'.join(parts[:idx]) for idx in xrange(1, len(parts)+1))

    versions = {}
    for module_name in ext_module_list:
        if module_name not in _VERSION_CACHE:
            try:
                __import__(module_name)
            except ImportError:
                continue
            app = sys.modules[module_name]
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
                    version = None
            else:
                version = None

            if isinstance(version, (list, tuple)):
                version = '.'.join(str(o) for o in version)
            _VERSION_CACHE[module_name] = version
        else:
            version = _VERSION_CACHE[module_name]
        if version is None:
            continue
        versions[module_name] = version
    return versions

def get_signature(key, message, timestamp):
    return hmac.new(key, '%s %s' % (timestamp, message), hashlib.sha1).hexdigest()

def get_auth_header(signature, timestamp, client):
    return 'Sentry sentry_signature=%s, sentry_timestamp=%s, raven=%s' % (
        signature,
        timestamp,
        raven.VERSION,
    )
