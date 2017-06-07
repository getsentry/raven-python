# -*- coding: utf-8 -*-
from __future__ import absolute_import
"""
raven.contrib.zconfig
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2013 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
import ZConfig.components.logger.factory
import raven.handlers.logging


class Factory(ZConfig.components.logger.factory.Factory):

    def getLevel(self):
        return self.section.level

    def create(self):
        return raven.handlers.logging.SentryHandler(**self.section.__dict__)

    def __init__(self, section):
        ZConfig.components.logger.factory.Factory.__init__(self)
        self.section = section
