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


class Transport(object):
    def check_scheme(self, url):
        if url.scheme != self.scheme:
            raise InvalidScheme()


class UDPTransport(Transport):
    interface.implements(ITransport)
    interface.classProvides(ITransportFactory)

    scheme = 'udp'

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


class HTTPTransport(Transport):
    interface.implements(ITransport)
    interface.classProvides(ITransportFactory)

    scheme = 'udp'

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


class TransportRegistry(object):
    def __init__(self):
        # setup a default list of senders
        self._schemes = {'http': HTTPTransport, 'udp': UDPTransport}

    def register_scheme(self, scheme, cls):
        """
        It is possible to inject new schemes at runtime
        """
        if scheme in self._schemes:
            raise DuplicateScheme()

        self._schemes[scheme] = cls

    def get_transport(self, scheme):
        return self._schemes[scheme]
