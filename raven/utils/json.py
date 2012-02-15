"""
raven.utils.json
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import datetime
import uuid

try:
    from __future__ import absolute_import
    import json
except ImportError:
    import simplejson as json

class BetterJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return obj.hex
        elif isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        elif isinstance(obj, (set, frozenset)):
            return list(obj)
        return super(BetterJSONEncoder, self).default(obj)


def better_decoder(data):
    return data


def dumps(value, **kwargs):
    return json.dumps(value, cls=BetterJSONEncoder, **kwargs)


def loads(value, **kwargs):
    return json.loads(value, object_hook=better_decoder)
