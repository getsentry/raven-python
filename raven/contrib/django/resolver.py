from __future__ import absolute_import

import re

from django.urls import get_resolver, Resolver404


class RouteResolver(object):
    _optional_group_matcher = re.compile(r'\(\?\:([^\)]+)\)')
    _named_group_matcher = re.compile(r'\(\?P<(\w+)>[^\)]+\)')
    _non_named_group_matcher = re.compile(r'\([^\)]+\)')
    # [foo|bar|baz]
    _either_option_matcher = re.compile(r'\[([^\]]+)\|([^\]]+)\]')
    _camel_re = re.compile(r'([A-Z]+)([a-z])')

    _cache = {}

    def _simplify(self, pattern):
        """
        Clean up urlpattern regexes into something readable by humans:

        From:
        > "^(?P<sport_slug>\w+)/athletes/(?P<athlete_slug>\w+)/$"

        To:
        > "{sport_slug}/athletes/{athlete_slug}/"
        """
        # remove optional params
        pattern = self._optional_group_matcher.sub(lambda m: '[%s]' % m.group(1), pattern)

        # handle named groups first
        pattern = self._named_group_matcher.sub(lambda m: '{%s}' % m.group(1), pattern)

        # handle non-named groups
        pattern = self._non_named_group_matcher.sub("{var}", pattern)

        # handle optional params
        pattern = self._either_option_matcher.sub(lambda m: m.group(1), pattern)

        # clean up any outstanding regex-y characters.
        pattern = pattern.replace('^', '').replace('$', '') \
            .replace('?', '').replace('//', '/').replace('\\', '')
        if not pattern.startswith('/'):
            pattern = '/' + pattern
        return pattern

    def resolve(self, path, urlconf=None):
        # TODO(dcramer): it'd be nice to pull out parameters
        # and make this a normalized path
        resolver = get_resolver(urlconf)
        match = resolver.regex.search(path)
        if match:
            new_path = path[match.end():]
            for pattern in resolver.url_patterns:
                try:
                    sub_match = pattern.resolve(new_path)
                except Resolver404:
                    continue
                if sub_match:
                    pattern = pattern.regex.pattern
                    try:
                        return self._cache[pattern]
                    except KeyError:
                        pass

                    pattern_name = self._simplify(pattern)
                    self._cache[pattern] = pattern
                    return pattern_name
        return path
