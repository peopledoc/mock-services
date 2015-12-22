# -*- coding: utf-8 -*-
import json
import logging

from functools import wraps

from .exceptions import Http400
from .exceptions import Http401
from .exceptions import Http403
from .exceptions import Http404
from .exceptions import Http405
from .exceptions import Http409
from .exceptions import Http500
from .mock import start_http_mock
from .mock import stop_http_mock


logger = logging.getLogger(__name__)


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
            return 400, {}, 'Bad Request'
        except Http401:
            return 401, {}, 'Unauthorized'
        except Http403:
            return 403, {}, 'Forbidden'
        except Http404:
            return 404, {}, 'Not Found'
        except Http405:
            return 405, {}, 'Method Not Allowed'
        except Http409:
            return 409, {}, 'Conflict'
        except (Exception, Http500) as e:
            logger.exception(e)
            return 500, {}, 'Internal Server Error'
    return wrapped


def to_json(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        status_code, headers, data = f(*args, **kwargs)
        # traped error are not json by default
        if status_code >= 400:
            data = {'error': data}
        return status_code, headers, json.dumps(data)
    return wrapped
