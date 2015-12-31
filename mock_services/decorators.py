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
from .helpers import start_http_mock
from .helpers import stop_http_mock


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
    def wrapped(request, context, *args, **kwargs):
        try:
            return f(request, context, *args, **kwargs)
        except Http400:
            context.status_code = 400
            return 'Bad Request'
        except Http401:
            context.status_code = 401
            return 'Unauthorized'
        except Http403:
            context.status_code = 403
            return 'Forbidden'
        except Http404:
            context.status_code = 404
            return 'Not Found'
        except Http405:
            context.status_code = 405
            return 'Method Not Allowed'
        except Http409:
            context.status_code = 409
            return 'Conflict'
        except (Exception, Http500) as e:
            logger.exception(e)
            context.status_code = 500
            return 'Internal Server Error'
    return wrapped


def to_json(f):
    @wraps(f)
    def wrapped(request, context, *args, **kwargs):
        data = f(request, context, *args, **kwargs)
        # traped error are not json by default
        if context.status_code >= 400:
            data = {'error': data}
        return json.dumps(data)
    return wrapped
