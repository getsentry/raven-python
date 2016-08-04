from __future__ import absolute_import

from raven.utils.conf import convert_options


def test_convert_options_parses_dict():
    options = convert_options({
        'SENTRY_FOO': 'foo',
        'FOO': 'bar',
        'SENTRY_RELEASE': 'a',
        'SENTRY_IGNORE_EXCEPTIONS': [
            'b',
        ]
    }, defaults={'environment': 'production'})

    assert options['release'] == 'a'
    assert options['ignore_exceptions'] == [
        'b',
    ]
    assert options['environment'] == 'production'
