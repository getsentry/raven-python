import urllib2
from socket import socket, AF_INET, SOCK_DGRAM, error as socket_error

class UDPSender(object):
    def __init__(self, parsed_url, data, headers):
        self._parsed_url = parsed_url
        self._data = data
        self._auth_header = headers.get('X-Sentry-Auth')
        self.udp_socket = None

    def send(self):
        if self._auth_header is None:
            # silently ignore attempts to send messages without an auth header
            return

        host, port = self._parsed_url.netloc.split(':')
        if self.udp_socket is None:
            self.udp_socket = socket(AF_INET, SOCK_DGRAM)
            self.udp_socket.setblocking(False)
        try:
            self.udp_socket.sendto(self._auth_header + '\n\n' + self._data, (host, int(port)))
        except socket_error:
            pass
        finally:
            # as far as I understand things this simply can't happen, but still, it can't hurt
            self.udp_socket.close()
            self.udp_socket = None

class HTTPSender(object):
    def __init__(self, parsed_url, data, headers):
        self._parsed_url = parsed_url
        self._url = parsed_url.geturl()
        self._data = data
        self._headers = headers

    def send(self):
        # , url, data, headers={}):
        """
        Sends a request to a remote webserver using HTTP POST.
        """
        req = urllib2.Request(self._url, headers=self._headers)
        try:
            response = urllib2.urlopen(req, self._data, self.timeout).read()
        except:
            response = urllib2.urlopen(req, self._data).read()
        return response



