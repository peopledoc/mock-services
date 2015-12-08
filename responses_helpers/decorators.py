# -*- coding: utf-8 -*-
import json

from functools import wraps

from .exceptions import Http400
from .exceptions import Http404
from .exceptions import Http409
from .exceptions import Http500
from .mock import start_http_mock
from .mock import stop_http_mock


def no_http_mock(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        stopped = stop_http_mock()
        r = f(*args, **kwargs)
        if stopped:
            start_http_mock()
        return r
    return wrapped


def with_http_mock(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        started = start_http_mock()
        return f(*args, **kwargs)
        if started:
            stop_http_mock()
    return wrapped


def trap_errors(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Http400:
            return 400, {}, {'error': 'validation error'}
        except Http404:
            return 404, {}, {'error': 'not found'}
        except Http409:
            return 409, {}, {'error': 'conflict'}
        except Http500:
            return 500, {}, {'error': 'API error'}
    return wrapped


def to_json(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        status_code, headers, data = f(*args, **kwargs)
        return status_code, headers, json.dumps(data)
    return wrapped
