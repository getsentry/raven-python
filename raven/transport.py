import urllib2
from socket import socket, AF_INET, SOCK_DGRAM, error as socket_error

class UDPSender(object):
    def __init__(self, parsed_url):
        self._parsed_url = parsed_url

    def send(self, data, headers):
        auth_header = headers.get('X-Sentry-Auth')
        udp_socket = None

        if auth_header is None:
            # silently ignore attempts to send messages without an auth header
            return

        host, port = self._parsed_url.netloc.split(':')
        if udp_socket is None:
            udp_socket = socket(AF_INET, SOCK_DGRAM)
            udp_socket.setblocking(False)
        try:
            udp_socket.sendto(auth_header + '\n\n' + data, (host, int(port)))
        except socket_error:
            pass
        finally:
            # as far as I understand things this simply can't happen, but still, it can't hurt
            udp_socket.close()
            self.udp_socket = None

class HTTPSender(object):
    def __init__(self, parsed_url):
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



