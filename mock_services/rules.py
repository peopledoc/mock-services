# -*- coding: utf-8 -*-
import logging
import re

from copy import deepcopy
from functools import partial

from requests_mock.response import _BODY_ARGS

from . import http_mock
from . import service
from . import storage


logger = logging.getLogger(__name__)

METHODS = [
    'LIST',  # custom
    'GET',
    'HEAD',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
]


def reset_rules():
    storage.reset()
    http_mock.reset()


def update_http_rules(rules, content_type='text/plain'):
    """Adds rules to global http mock.

    It permits to set mock in a more global way than decorators, cf.:
    https://github.com/openstack/requests-mock

    Here we assume urls in the passed dict are regex we recompile before adding
    a rule.

    Rules example:

    >>> def fake_duckduckgo_cb(request):
    ...     return 200, {}, 'Coincoin!'

    >>> rules = [
        {
            'method': 'GET',
            'status_code': 200,
            'text': 'I am watching you',
            'url': r'^https://www.google.com/#q='
        },
        {
            'method': 'GET',
            'text': fake_duckduckgo_cb,
            'url': r'^https://duckduckgo.com/?q='
        },
    ]

    """
    for kw in deepcopy(rules):

        kw['url'] = re.compile(kw['url'])

        # ensure headers dict for at least have a default content type
        if 'Content-Type' not in kw.get('headers', {}):
            kw['headers'] = dict(kw.get('headers', {}), **{
                'Content-Type': content_type,
            })

        method = kw.pop('method')
        url = kw.pop('url')

        http_mock.register_uri(method, url, **kw)


def update_rest_rules(rules, content_type='application/json'):

    http_rules = []

    for kw in deepcopy(rules):

        if kw['method'] not in METHODS:
            raise NotImplementedError('invalid method "{method}" for: {url}'.format(**kw))  # noqa

        # set callback if does not has one
        if not any(x for x in _BODY_ARGS if x in kw):
            _cb = getattr(service, '{0}_cb'.format(kw['method'].lower()))
            kw['text'] = partial(_cb, **kw.copy())

        # no content
        if kw['method'] in ['DELETE', 'HEAD'] \
                and'Content-Type' not in kw.get('headers', {}):
            kw['headers'] = dict(kw.get('headers', {}), **{
                'Content-Type': 'text/plain',
            })

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

    update_http_rules(http_rules, content_type=content_type)
