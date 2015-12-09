# -*- coding: utf-8 -*-
import pkg_resources

from .rules import update_http_rules
from .rules import update_rest_rules
from .rules import reset_rules

from .mock import is_http_mock_started
from .mock import start_http_mock
from .mock import stop_http_mock

from .decorators import no_http_mock
from .decorators import with_http_mock


__all__ = [
    'reset_rules',
    'update_http_rules',
    'update_rest_rules',

    'is_http_mock_started',
    'start_http_mock',
    'stop_http_mock',

    'no_http_mock',
    'with_http_mock',
]

__version__ = pkg_resources.get_distribution(__package__).version
