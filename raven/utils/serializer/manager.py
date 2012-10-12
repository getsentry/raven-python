"""
raven.utils.serializer.manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
import logging

__all__ = ('register', 'transform')

logger = logging.getLogger('sentry.errors.serializer')


class SerializationManager(object):
    def __init__(self):
        self.__registry = []
        self.__serializers = {}

    @property
    def serializers(self):
        # XXX: Would serializers ever need state that we shouldnt cache them?
        for serializer in self.__registry:
            yield serializer

    def register(self, serializer):
        if serializer not in self.__registry:
            self.__registry.append(serializer)
        return serializer


class Serializer(object):
    def __init__(self, manager):
        self.manager = manager
        self.context = {}
        self.serializers = []
        for serializer in manager.serializers:
            self.serializers.append(serializer(self))

    def transform(self, value):
        """
        Primary function which handles recursively transforming
        values via their serializers
        """
        if value is None:
            return None

        objid = id(value)
        if objid in self.context:
            return '<...>'
        self.context[objid] = 1

        # TODO: do we still need this code? context seems to handle it
        # if any(value is s for s in self.stack):
        #     ret = 'cycle'
        # self.stack.append(value)

        try:
            for serializer in self.serializers:
                if serializer.can(value):
                    try:
                        return serializer.serialize(value)
                    except Exception, e:
                        logger.exception(e)
                        return u'<BadSerializable: %s>' % type(value)

            # if all else fails, lets use the repr of the object
            try:
                return self.transform(repr(value))
            except Exception, e:
                logger.exception(e)
                # It's common case that a model's __unicode__ definition may try to query the database
                # which if it was not cleaned up correctly, would hit a transaction aborted exception
                return u'<BadRepr: %s>' % type(value)
        finally:
            del self.context[objid]


manager = SerializationManager()
register = manager.register


def transform(value, manager=manager):
    serializer = Serializer(manager)
    return serializer.transform(value)
