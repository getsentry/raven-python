from __future__ import absolute_import

from datetime import datetime, timedelta


epoch = datetime(1970, 1, 1)


def to_timestamp(value):
    return (value - epoch).total_seconds()


def to_datetime(value):
    return epoch + timedelta(seconds=value)
