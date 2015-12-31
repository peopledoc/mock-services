from requests_mock import Adapter
from requests_mock import MockerCore


class HttpAdapter(Adapter):

    def get_rules(self):
        return self._matchers

    def reset(self):
        self._matchers = []


_adapter = HttpAdapter()


class HttpMock(MockerCore):

    def __init__(self, *args, **kwargs):
        super(HttpMock, self).__init__(*args, **kwargs)
        self._adapter = _adapter

    def is_started(self):
        return self._real_send

    def set_allow_external(self, allow):
        """Set flag to authorize external calls when no matching mock.

        Will raise an requests_mock.exceptions.NoMockAddress error otherwhise.
        """
        self._real_http = allow


_http_mock = HttpMock()

__all__ = []

# expose mocker instance public methods
for __attr in [a for a in dir(_http_mock) if not a.startswith('_')]:
    __all__.append(__attr)
    globals()[__attr] = getattr(_http_mock, __attr)

# expose adapter instance public methods
for __attr in [a for a in dir(_adapter) if not a.startswith('_')]:
    __all__.append(__attr)
    globals()[__attr] = getattr(_adapter, __attr)
