"""
raven.transport.udp
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.transport.base import Transport

try:
    # Google App Engine blacklists parts of the socket module, this will prevent
    # it from blowing up.
    from socket import socket, AF_INET, AF_INET6, SOCK_DGRAM, has_ipv6, getaddrinfo, error as socket_error
    has_socket = True
except Exception:
    has_socket = False


class BaseUDPTransport(Transport):
    def __init__(self, parsed_url):
        super(BaseUDPTransport, self).__init__()
        self.check_scheme(parsed_url)
        self._parsed_url = parsed_url

    def _get_addr_info(self, host, port):
        """
        Selects the address to connect to, based on the supplied host/port
        information. This method prefers v4 addresses, and will only return
        a v6 address if it's the only option.
        """
        addresses = getaddrinfo(host, port)
        v4_addresses = [info for info in addresses if info[0] == AF_INET]
        if has_ipv6:
            v6_addresses = [info for info in addresses if info[0] == AF_INET6]
            if v6_addresses and not v4_addresses:
                # The only time we return a v6 address is if it's the only option
                return v6_addresses[0]
        return v4_addresses[0]

    def send(self, data, headers):
        auth_header = headers.get('X-Sentry-Auth')

        if auth_header is None:
            # silently ignore attempts to send messages without an auth header
            return

        host, port = self._parsed_url.netloc.rsplit(':')
        addr_info = self._get_addr_info(host, int(port))
        self._send_data(auth_header + '\n\n' + data, addr_info)


class UDPTransport(BaseUDPTransport):
    scheme = ['udp']

    def __init__(self, parsed_url):
        super(UDPTransport, self).__init__(parsed_url)
        if not has_socket:
            raise ImportError('UDPTransport requires the socket module')

    def _send_data(self, data, addr_info):
        udp_socket = None
        af = addr_info[0]
        addr = addr_info[4]
        try:
            udp_socket = socket(af, SOCK_DGRAM)
            udp_socket.setblocking(False)
            udp_socket.sendto(data, addr)
        except socket_error:
            # as far as I understand things this simply can't happen,
            # but still, it can't hurt
            pass
        finally:
            # Always close up the socket when we're done
            if udp_socket is not None:
                udp_socket.close()
                udp_socket = None
