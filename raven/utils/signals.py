from __future__ import absolute_import
import blinker


raven_signals = blinker.Namespace()

logging_configured = raven_signals.signal('logging_configured')
