from raven.utils import six


class APIError(Exception):
    def __init__(self, message, code=0):
        self.code = code
        self.message = message

    def __unicode__(self):
        return six.text_type("%s: %s" % (self.message, self.code))


class RateLimited(APIError):
    pass
