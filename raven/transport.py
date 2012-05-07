import urllib2
from socket import socket, AF_INET, SOCK_DGRAM, error as socket_error
from zope import interface


class InvalidScheme(ValueError):
    """
    Raised when a transport is constructed using a URI which is not
    handled by the transport
    """


class DuplicateScheme(StandardError):
    """
    Raised when registering a handlers for a particular scheme which
    is already registered
    """
    pass


class ITransportFactory(interface.Interface):
    def __call__(uri):
        """
        :param uri: the server url to that an instance of ITransport
                    will actually use
        """
        pass


class ITransport(interface.Interface):
    scheme = interface.Attribute("Scheme that this transport handles")

    def send(data, headers):
        """
        :param data: data to be sent to the server as the
                     payload
        :type data: string

        :param headers: headers that a transport may use when sending
                        to the server
        :type headers: dictionary
        :returns: int - result code from the transmission or None if
                  no result code is available
        """

    def compute_scope(url, scope):
        """
        Update or create a new scope with the following keys:

        * SENTRY_SERVERS
        * SENTRY_PROJECT
        * SENTRY_PUBLIC_KEY
        * SENTRY_SECRET_KEY
        """


class Transport(object):
    def check_scheme(self, url):
        if url.scheme not in self.scheme:
            raise InvalidScheme()


class UDPTransport(Transport):
    interface.implements(ITransport)
    interface.classProvides(ITransportFactory)

    scheme = ['udp']

    def __init__(self, parsed_url):
        self.check_scheme(parsed_url)

        self._parsed_url = parsed_url

    def send(self, data, headers):
        auth_header = headers.get('X-Sentry-Auth')

        if auth_header is None:
            # silently ignore attempts to send messages without an auth header
            return

        host, port = self._parsed_url.netloc.split(':')

        udp_socket = None
        try:
            udp_socket = socket(AF_INET, SOCK_DGRAM)
            udp_socket.setblocking(False)
            udp_socket.sendto(auth_header + '\n\n' + data, (host, int(port)))
        except socket_error:
            # as far as I understand things this simply can't happen,
            # but still, it can't hurt
            pass
        finally:
            # Always close up the socket when we're done
            if udp_socket != None:
                udp_socket.close()
                udp_socket = None

    def compute_scope(self, url, scope):
        netloc = url.hostname

        path_bits = url.path.rsplit('/', 1)
        if len(path_bits) > 1:
            path = path_bits[0]
        else:
            path = ''
        project = path_bits[-1]

        if not all([netloc, project, url.username, url.password]):
            raise ValueError('Invalid Sentry DSN: %r' % url.geturl())

        server = '%s://%s%s/api/store/' % (url.scheme, netloc, path)
        scope.update({
            'SENTRY_SERVERS': [server],
            'SENTRY_PROJECT': project,
            'SENTRY_PUBLIC_KEY': url.username,
            'SENTRY_SECRET_KEY': url.password,
        })
        return scope


class HTTPTransport(Transport):
    interface.implements(ITransport)
    interface.classProvides(ITransportFactory)

    scheme = ['http', 'https']

    def __init__(self, parsed_url):
        self.check_scheme(parsed_url)

        self._parsed_url = parsed_url
        self._url = parsed_url.geturl()

    def send(self, data, headers):
        """
        Sends a request to a remote webserver using HTTP POST.
        """
        req = urllib2.Request(self._url, headers=headers)
        try:
            response = urllib2.urlopen(req, data, self.timeout).read()
        except:
            response = urllib2.urlopen(req, data).read()
        return response

    def compute_scope(self, url, scope):
        netloc = url.hostname
        if (url.scheme == 'http' and url.port and url.port != 80) or \
           (url.scheme == 'https' and url.port and url.port != 443):
            netloc += ':%s' % url.port

        path_bits = url.path.rsplit('/', 1)
        if len(path_bits) > 1:
            path = path_bits[0]
        else:
            path = ''
        project = path_bits[-1]

        if not all([netloc, project, url.username, url.password]):
            raise ValueError('Invalid Sentry DSN: %r' % url.geturl())

        server = '%s://%s%s/api/store/' % (url.scheme, netloc, path)
        scope.update({
            'SENTRY_SERVERS': [server],
            'SENTRY_PROJECT': project,
            'SENTRY_PUBLIC_KEY': url.username,
            'SENTRY_SECRET_KEY': url.password,
        })
        return scope


class TransportRegistry(object):
    def __init__(self):
        # setup a default list of senders
        self._schemes = {'http': HTTPTransport,
                         'https': HTTPTransport,
                         'udp': UDPTransport}

    def register_scheme(self, scheme, cls):
        """
        It is possible to inject new schemes at runtime
        """
        if scheme in self._schemes:
            raise DuplicateScheme()

        self._schemes[scheme] = cls

    def supported_scheme(self, scheme):
        return scheme in self._schemes

    def get_transport(self, scheme):
        return self._schemes[scheme]

    def compute_scope(self, url, scope):
        """
        Compute a scope dictionary.  This may be overridden by custom
        transports
        """
        transport = self._schemes[url.scheme](url)
        return transport.compute_scope(url, scope)
