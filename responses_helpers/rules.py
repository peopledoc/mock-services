# -*- coding: utf-8 -*-
import logging
import re

import responses


logger = logging.getLogger(__name__)


def update_http_rules(rules, content_type='application/json'):
    """Adds rules to global responses mock.

    It permits to set mock in a more global way than decorators, cf.:
    https://github.com/getsentry/responses

    Here we assume urls in the passed dict are regex we recompile before adding
    a rule.

    Rules example:

    >>> def fake_duckduckgo_cb(request):
    ...     return 200, {}, 'Coincoin!'

    >>> rules = [
        {
            'body': 'I am watching you',
            'method': 'GET',
            'status': 200,
            'url': r'^https://www.google.com/#q='
        },
        {
            'callback': fake_duckduckgo_cb,
            'method': 'GET',
            'url': r'^https://duckduckgo.com/?q='
        },
    ]

    """
    for i, kw in enumerate(rules):

        logger.debug('{} {}'.format(kw['method'].upper(), kw['url']))

        kw['url'] = re.compile(kw['url'])

        if 'content_type' not in kw:
            kw['content_type'] = content_type

        add_func = 'add_callback' if 'callback' in kw else 'add'
        getattr(responses, add_func)(match_querystring=True, **kw)
