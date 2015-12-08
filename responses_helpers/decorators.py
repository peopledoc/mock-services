# -*- coding: utf-8 -*-
from functools import wraps

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
