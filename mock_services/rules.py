# -*- coding: utf-8 -*-
import logging
import re

from functools import partial

import responses

from . import service
from . import storage


logger = logging.getLogger(__name__)


def reset_rules():
    responses.reset()
    storage.reset()


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

        if kw['method'] not in ['GET', 'POST', 'PATCH', 'DELETE']:
            logger.error('skip! invalid method for: %s', kw)
            continue

        logger.debug('%s %s', kw['method'], kw['url'])

        kw['url'] = re.compile(kw['url'])

        if 'content_type' not in kw:
            kw['content_type'] = content_type

        add_func = 'add_callback' if 'callback' in kw else 'add'
        getattr(responses, add_func)(match_querystring=True, **kw)


def update_rest_rules(rules, content_type='application/json'):

    http_rules = []

    for kw in rules:

        if kw['method'] not in ['LIST', 'GET', 'POST', 'PATCH', 'DELETE']:
            logger.error('skip! invalid method for: %s', kw)
            continue

        # set callback if does not has one
        if 'callback' not in kw:
            _cb = getattr(service, '{0}_cb'.format(kw['method'].lower()))
            kw['callback'] = partial(_cb, **kw.copy())

        # restore standard method
        if kw['method'] == 'LIST':
            kw['method'] = 'GET'

        # clean extra kwargs
        kw.pop('attrs', None)
        kw.pop('id_name', None)
        kw.pop('id_factory', None)
        kw.pop('validators', None)

        # update http_rules
        http_rules.append(kw)

    update_http_rules(rules, content_type=content_type)
