from __future__ import absolute_import

import warnings

from raven._compat import PY2, text_type
from raven.exceptions import InvalidDsn
from raven.transport.threaded import ThreadedHTTPTransport
from raven.utils.encoding import to_string
from raven.utils.urlparse import parse_qsl, urlparse

ERR_UNKNOWN_SCHEME = 'Unsupported Sentry DSN scheme: {0} ({1})'

DEFAULT_TRANSPORT = ThreadedHTTPTransport


class RemoteConfig(object):
    def __init__(self, base_url=None, project=None, public_key=None,
                 secret_key=None, transport=None, options=None):
        if base_url:
            base_url = base_url.rstrip('/')
            store_endpoint = '%s/api/%s/store/' % (base_url, project)
        else:
            store_endpoint = None

        self.base_url = base_url
        self.project = project
        self.public_key = public_key
        self.secret_key = secret_key
        self.options = options or {}
        self.store_endpoint = store_endpoint

        self._transport_cls = transport or DEFAULT_TRANSPORT

    def __unicode__(self):
        return text_type(self.base_url)

    def is_active(self):
        return all([self.base_url, self.project, self.public_key, self.secret_key])

    # TODO(dcramer): we dont want transports bound to a URL
    def get_transport(self):
        if not self.store_endpoint:
            return

        if not hasattr(self, '_transport'):
            parsed = urlparse(self.store_endpoint)
            self._transport = self._transport_cls(parsed, **self.options)
        return self._transport

    def get_public_dsn(self):
        url = urlparse(self.base_url)
        netloc = url.hostname
        if url.port:
            netloc += ':%s' % url.port
        return '//%s@%s%s/%s' % (self.public_key, netloc, url.path, self.project)

    @classmethod
    def from_string(cls, value, transport=None, transport_registry=None):
        # in Python 2.x sending the DSN as a unicode value will eventually
        # cause issues in httplib
        if PY2:
            value = to_string(value)

        url = urlparse(value)

        if url.scheme not in ('http', 'https'):
            warnings.warn('Transport selection via DSN is deprecated. You should explicitly pass the transport class to Client() instead.')

        if transport is None:
            if not transport_registry:
                from raven.transport import TransportRegistry, default_transports
                transport_registry = TransportRegistry(default_transports)

            if not transport_registry.supported_scheme(url.scheme):
                raise InvalidDsn(ERR_UNKNOWN_SCHEME.format(url.scheme, value))

            transport = transport_registry.get_transport_cls(url.scheme)

        netloc = url.hostname
        if url.port:
            netloc += ':%s' % url.port

        path_bits = url.path.rsplit('/', 1)
        if len(path_bits) > 1:
            path = path_bits[0]
        else:
            path = ''
        project = path_bits[-1]

        if not all([netloc, project, url.username, url.password]):
            raise InvalidDsn('Invalid Sentry DSN: %r' % url.geturl())

        base_url = '%s://%s%s' % (url.scheme.rsplit('+', 1)[-1], netloc, path)

        return cls(
            base_url=base_url,
            project=project,
            public_key=url.username,
            secret_key=url.password,
            options=dict(parse_qsl(url.query)),
            transport=transport,
        )
