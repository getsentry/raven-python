from __future__ import absolute_import
import urlparse as _urlparse


def register_scheme(scheme):
    for method in filter(lambda s: s.startswith('uses_'), dir(_urlparse)):
        getattr(_urlparse, method).append(scheme)


urlparse = _urlparse.urlparse
