"""
raven.contrib.tornado
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details
:license: BSD, see LICENSE for more details
"""
from __future__ import absolute_import

import time
import warnings

import raven
from raven.base import Client
from raven.utils import get_auth_header
from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPError


class AsyncSentryClient(Client):
    """A mixin class that could be used along with request handlers to
    asynchronously send errors to sentry. The client also captures the
    information from the request handlers
    """
    def capture(self, *args, **kwargs):
        """
        Takes the same arguments as the super function in :py:class:`Client`
        and extracts the keyword argument callback which will be called on
        asynchronous sending of the request

        :return: a 32-length string identifying this event and checksum
        """
        data = self.build_msg(*args, **kwargs)

        self.send(callback=kwargs.get('callback', None), **data)

        return (data['event_id'], data['checksum'])

    def send(self, public_key=None, auth_header=None, callback=None, **data):
        """
        Serializes the message and passes the payload onto ``send_encoded``.
        """
        message = self.encode(data)

        try:
            return self.send_encoded(
                message, public_key=public_key, auth_header=auth_header,
                callback=callback
            )
        except TypeError:
            # Make the assumption that public_key wasnt supported
            warnings.warn(
                '%s.send_encoded needs updated to support ``**kwargs``' % (
                    type(self).__name__,
                ), DeprecationWarning
            )
            return self.send_encoded(message, callback=callback)

    def send_encoded(self, message, public_key=None, auth_header=None, **kwargs):
        """
        Given an already serialized message, signs the message and passes the
        payload off to ``send_remote`` for each server specified in the servers
        configuration.

        callback can be specified as a keyword argument
        """
        if not self.servers:
            warnings.warn('Raven client has no remote servers configured')
            return

        if not auth_header:
            timestamp = time.time()
            auth_header = get_auth_header(
                protocol=self.protocol_version,
                timestamp=timestamp,
                client='raven-python/%s' % (raven.VERSION,),
                api_key=public_key or self.public_key
            )

        for url in self.servers:
            headers = {
                'X-Sentry-Auth': auth_header,
                'Content-Type': 'application/octet-stream',
            }

            self.send_remote(
                url=url, data=message, headers=headers,
                callback=kwargs.get('callback', None)
            )

    def send_remote(self, url, data, headers={}, callback=None):
        if not self.state.should_try():
            message = self._get_log_message(data)
            self.error_logger.error(message)
            return

        try:
            self._send_remote(
                url=url, data=data, headers=headers, callback=callback
            )
        except HTTPError, e:
            body = e.response.body
            self.error_logger.error(
                'Unable to reach Sentry log server: %s '
                '(url: %%s, body: %%s)' % (e,),
                url, body, exc_info=True,
                extra={'data': {'body': body, 'remote_url': url}}
            )
        except Exception, e:
            self.error_logger.error(
                'Unable to reach Sentry log server: %s (url: %%s)' % (e,),
                url, exc_info=True, extra={'data': {'remote_url': url}}
            )
            message = self._get_log_message(data)
            self.error_logger.error('Failed to submit message: %r', message)
            self.state.set_fail()
        else:
            self.state.set_success()

    def _send_remote(self, url, data, headers=None, callback=None):
        """
        Initialise a Tornado AsyncClient and send the reuqest to the sentry
        server. If the callback is a callable, it will be called with the
        response.
        """
        if headers is None:
            headers = {}

        return AsyncHTTPClient().fetch(
            url, callback, method="POST", body=data, headers=headers
        )



class SentryMixin(object):
    """
    A mixin class that extracts information from the Request in a Request
    Handler to capture and send to sentry. This mixin class is designed to be
    used along with `tornado.web.RequestHandler`

    .. code-block:: python
        :emphasize-lines: 6

        class MyRequestHandler(SentryMixin, tornado.web.RequestHandler):
            def get(self):
                try:
                    fail()
                except Exception, e:
                    self.captureException(sys.exc_info())


    While the above example would result in sequential execution, an example
    for asynchronous use would be

    .. code-block:: python
        :emphasize-lines: 6

        class MyRequestHandler(SentryMixin, tornado.web.RequestHandler):

            @tornado.web.asynchronous
            @tornado.gen.engine
            def get(self):
                # Do something and record a message in sentry
                response = yield tornado.gen.Task(
                    self.captureMessage, "Did something really important"
                )
                self.write("Your request to do something important is done")
                self.finish()


    The mixin assumes that the application will have an attribute called
    `sentry_client`, which should be an instance of
    :py:class:`AsyncSentryClient`. This can be changed by implementing your
    own get_sentry_client method on your request handler.
    """

    def get_sentry_client(self):
        """
        Returns the sentry client configured in the application. If you need
        to change the behaviour to do something else to get the client, then
        subclass this method
        """
        return self.application.sentry_client

    def get_sentry_data_from_request(self):
        """
        Extracts the data required for 'sentry.interfaces.Http' from the
        current request being handled by the request handler

        :param return: A dictionary.
        """
        return {
            'sentry.interfaces.Http': {
                'url':  self.request.full_url(),
                'method': self.request.method,
                'data': self.request.arguments,
                'query_string': self.request.query,
                'cookies': self.request.headers.get('Cookie', None),
                'headers': dict(self.request.headers),
            }
        }

    def get_sentry_user_info(self):
        """
        Data for sentry.interfaces.User

        Default implementation only sends `is_authenticated` by checking if
        `tornado.web.RequestHandler.get_current_user` tests postitively for on
        Truth calue testing
        """
        return {
            'sentry.interfaces.User': {
                'is_authenticated': True if self.get_current_user() else False
            }
        }

    def get_sentry_extra_info(self):
        """
        Subclass and implement this method if you need to send any extra
        information
        """
        return {
            'extra': {
            }
        }

    def capture(self, event_type, data=None, **kwargs):
        if data is None:
            data = {}

        # Update request data
        data.update(self.get_sentry_data_from_request())

        # update user data
        data.update(self.get_sentry_user_info())

        # Update extra data
        data.update(self.get_sentry_extra_info())

        client = self.get_sentry_client()
        return client.capture(event_type, data=data, **kwargs)

    def captureException(self, exc_info=None, **kwargs):
        return self.capture('Exception', exc_info=exc_info, **kwargs)

    def captureMessage(self, message, **kwargs):
        return self.capture('Message', message=message, **kwargs)

    def write_error(self, status_code, **kwargs):
        """Override implementation to report all exceptions to sentry.
        """
        rv = super(SentryMixin, self).write_error(status_code, **kwargs)
        self.captureException(exc_info=kwargs['exc_info'])
        return rv
