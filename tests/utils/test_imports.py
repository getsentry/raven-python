from __future__ import absolute_import

import six

import raven

from raven.utils.imports import import_string


def test_import_string():
    new_raven = import_string('raven')
    assert new_raven is raven

    # this will test unicode on python2
    new_raven = import_string(six.text_type('raven'))
    assert new_raven is raven

    new_client = import_string('raven.Client')
    assert new_client is raven.Client

    # this will test unicode on python2
    new_client = import_string(six.text_type('raven.Client'))
    assert new_client is raven.Client
