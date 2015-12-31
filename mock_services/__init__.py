# -*- coding: utf-8 -*-
import pkg_resources

from .decorators import no_http_mock
from .decorators import with_http_mock

from .helpers import is_http_mock_started
from .helpers import start_http_mock
from .helpers import stop_http_mock

from .rules import update_http_rules
from .rules import update_rest_rules
from .rules import reset_rules


__all__ = [
    'no_http_mock',
    'with_http_mock',

    'is_http_mock_started',
    'start_http_mock',
    'stop_http_mock',

    'reset_rules',
    'update_http_rules',
    'update_rest_rules',
]

__version__ = pkg_resources.get_distribution(__package__).version
