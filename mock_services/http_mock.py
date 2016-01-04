import requests
from requests.exceptions import ConnectionError

from requests_mock import Adapter
from requests_mock import MockerCore
from requests_mock.exceptions import NoMockAddress


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

        Will raise a ConnectionError otherwhise.
        """
        self._real_http = allow

    def _patch_real_send(self):

        _fake_send = requests.Session.send

        def _patched_fake_send(session, request, **kwargs):
            try:
                return _fake_send(session, request, **kwargs)
            except NoMockAddress:
                request = _adapter.last_request
                error_msg = 'Connection refused: {0} {1}'.format(
                    request.method,
                    request.url
                )
                response = ConnectionError(error_msg)
                response.request = request
                raise response

        requests.Session.send = _patched_fake_send

    def start(self):
        """Overrides default start behaviour by raising ConnectionError instead
        of custom requests_mock.exceptions.NoMockAddress.
        """
        super(HttpMock, self).start()
        self._patch_real_send()


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
