from raven import Client
from raven.contrib.transports.zeromq import ZmqPubTransport
import sys

Client.register_scheme('zmq+tcp', ZmqPubTransport)

uri = "zmq+tcp://127.0.0.1:5000"
c = Client(dsn=uri)
while True:
    try:
        5 / 0
    except:
        c.captureException(sys.exc_info())
