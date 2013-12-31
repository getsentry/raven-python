"""
raven.utils.json
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import codecs
import datetime
import uuid

try:
    import simplejson as json
except ImportError:
    import json

try:
    JSONDecodeError = json.JSONDecodeError
except AttributeError:
    JSONDecodeError = ValueError


class BetterJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return obj.hex
        elif isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif isinstance(obj, (set, frozenset)):
            return list(obj)
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        return super(BetterJSONEncoder, self).default(obj)


def better_decoder(data):
    return data


def dumps(value, **kwargs):
    try:
        return json.dumps(value, cls=BetterJSONEncoder, **kwargs)
    except:
        try:
            kwargs['encoding'] = 'safe-utf-8'
            return json.dumps(value, cls=BetterJSONEncoder, **kwargs)
        except:
            return "could not json encode: %s" % str(value)


def loads(value, **kwargs):
    return json.loads(value, object_hook=better_decoder)


_utf8_encoder = codecs.getencoder('utf-8')


def safe_encode(input, errors='backslashreplace'):
    return _utf8_encoder(input, errors)


_utf8_decoder = codecs.getdecoder('utf-8')


def safe_decode(input, errors='replace'):
    return _utf8_decoder(input, errors)


class Codec(codecs.Codec):

    def encode(self, input, errors='backslashreplace'):
        return safe_encode(input, errors)

    def decode(self, input, errors='replace'):
        return safe_decode(input, errors)


class IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=False):
        return safe_encode(input, self.errors)[0]


class IncrementalDecoder(codecs.IncrementalDecoder):
    def decode(self, input, final=False):
        return safe_decode(input, self.errors)[0]


class StreamWriter(Codec, codecs.StreamWriter):
    pass


class StreamReader(Codec, codecs.StreamReader):
    pass


def getregentry(name):
    if name != 'safe-utf-8':
        return None
    return codecs.CodecInfo(
        name='safe-utf-8',
        encode=safe_encode,
        decode=safe_decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )


codecs.register(getregentry)
