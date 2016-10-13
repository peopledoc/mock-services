# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import uuid

from collections import defaultdict
from functools import wraps
from itertools import count

from .exceptions import Http404
from .exceptions import Http409
from .exceptions import Http500


logger = logging.getLogger(__name__)


def check_conflict(f):
    @wraps(f)
    def wrapped(self, ctx, *args, **kwargs):
        ctx.id = str(ctx.id)
        if ctx.id in self._registry[ctx.key]:
            raise Http409
        return f(self, ctx, *args, **kwargs)
    return wrapped


def check_exist(f):
    @wraps(f)
    def wrapped(self, ctx, *args, **kwargs):
        ctx.id = str(ctx.id)
        if ctx.id not in self._registry[ctx.key]:
            raise Http404
        return f(self, ctx, *args, **kwargs)
    return wrapped


class Storage(object):

    _counter = None
    _registry = None

    def __init__(self):
        self.reset()

    @check_conflict
    def add(self, ctx, data):
        self._registry[ctx.key][ctx.id] = data
        return data

    @check_exist
    def get(self, ctx):
        return self._registry[ctx.key][ctx.id]

    def to_list(self, ctx):
        return list(self._registry[ctx.key].values())

    def next_id(self, id_factory):
        if id_factory == int:
            return next(self._counter)
        if id_factory == uuid.UUID:
            return str(uuid.uuid4())
        logger.error('invalid id factory: %s', id_factory)
        raise Http500

    @check_exist
    def remove(self, ctx):
        del self._registry[ctx.key][ctx.id]

    def reset(self):
        self._counter = count(start=1)
        self._registry = defaultdict(dict)

    @check_exist
    def update(self, ctx, data):
        self._registry[ctx.key][ctx.id].update(data)
        return self._registry[ctx.key][ctx.id]


_storage = Storage()

__all__ = []

# expose storage instance public methods
for __attr in (a for a in dir(_storage) if not a.startswith('_')):
    __all__.append(__attr)
    globals()[__attr] = getattr(_storage, __attr)
