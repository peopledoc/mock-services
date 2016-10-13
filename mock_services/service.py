# -*- coding: utf-8 -*-
import json
import logging
import re
try:
    from urllib import parse as urlparse
except ImportError:
    # Python 2
    import urlparse

import attr

from . import storage
from .decorators import to_json
from .decorators import trap_errors
from .exceptions import Http400
from .exceptions import Http404


logger = logging.getLogger(__name__)


@attr.s
class ResourceContext(object):
    hostname = attr.ib()
    resource = attr.ib()
    action = attr.ib(default='default')
    id = attr.ib(default=None)

    @property
    def key(self):
        return '{hostname}/{resource}/{action}'.format(**attr.asdict(self))


def parse_url(request, url_pattern, id=None, require_id=False):

    logger.debug('url_pattern: %s', url_pattern)
    logger.debug('url: %s', request.url)

    url_kw = re.compile(url_pattern).search(request.url).groupdict()
    logger.debug('url_kw: %s', url_kw)

    if 'resource' not in url_kw:
        raise Http404

    if require_id and 'id' not in url_kw:
        raise Http404

    hostname = urlparse.urlparse(request.url).hostname
    logger.debug('hostname: %s', hostname)

    action = url_kw.pop('action', 'default')
    logger.debug('action: %s', action)

    resource_context = ResourceContext(
        hostname=hostname,
        resource=url_kw.pop('resource'),
        action=action,
        id=url_kw.pop('id', id),
    )
    logger.debug('resource_context: %s', attr.asdict(resource_context))

    return resource_context


def validate_data(request, attrs=None, validators=None):

    logger.debug('attrs: %s', attrs)
    logger.debug('body: %s', request.body)

    data = json.loads(request.body)
    data_to_validate = {k: v
                        for k, v in data.items()
                        if k in (attrs or {}).keys()}
    logger.debug('data_to_validate: %s', data_to_validate)

    # missing field
    if attrs and not data_to_validate:
        raise Http400

    # invalid field
    if data_to_validate:
        try:
            attr.make_class("C", attrs)(**data_to_validate)
        except (TypeError, ValueError):
            raise Http400

    # custom validation
    for validate_func in (validators or []):
        validate_func(request)

    return data


@to_json
@trap_errors
def list_cb(request, context, url=None, **kwargs):
    resource_context = parse_url(request, url)
    context.status_code = 200
    return storage.to_list(resource_context)


@to_json
@trap_errors
def get_cb(request, context, url=None, **kwargs):
    resource_context = parse_url(request, url, require_id=True)
    context.status_code = 200
    return storage.get(resource_context)


@trap_errors
def head_cb(request, context, url=None, id_name='id', **kwargs):
    resource_context = parse_url(request, url, require_id=True)
    context.headers = dict(context.headers or {},
                           **{id_name: resource_context.id})
    context.status_code = 200
    return ''


@to_json
@trap_errors
def post_cb(request, context, url=None, id_name='id', id_factory=int,
            attrs=None, validators=None, **kwargs):

    data = validate_data(request, attrs=attrs, validators=validators)

    id = storage.next_id(id_factory)
    logger.debug('id: %s', id)

    data.update({
        id_name: id
    })
    logger.debug('data: %s', data)

    resource_context = parse_url(request, url, id=id)
    context.status_code = 201

    return storage.add(resource_context, data)


@to_json
@trap_errors
def patch_cb(request, context, url=None, attrs=None, validators=None,
             **kwargs):

    data = validate_data(request, attrs=attrs, validators=validators)
    logger.debug('data: %s', data)

    resource_context = parse_url(request, url, require_id=True)
    context.status_code = 200

    return storage.update(resource_context, data)


put_cb = patch_cb


@trap_errors
def delete_cb(request, context, url=None, **kwargs):
    resource_context = parse_url(request, url, require_id=True)
    context.status_code = 204
    return storage.remove(resource_context) or ''
