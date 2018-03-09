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


_http_adapter = HttpAdapter()


class HttpMock(MockerCore):

    def __init__(self, *args, **kwargs):
        super(HttpMock, self).__init__(*args, **kwargs)
        self._adapter = _http_adapter
        self._http_last_send = None

    def is_started(self):
        # requests_mock > 1.1 allows nested mocking
        # (see commit https://tinyurl.com/ya3ofy6s)
        # Old mechanism:
        #    MockerCore._real_send => original mocked send method
        # New mechanism:
        #    _original_send => original requests.Session.send method
        #    MockerCore._last_send => nested mock send method 
        return self._last_send is not None

    def set_allow_external(self, allow):
        """Set flag to authorize external calls when no matching mock.

        Will raise a ConnectionError otherwhise.
        """
        self._real_http = allow

    def _patch_last_send(self):
        self._http_last_send = requests.Session.send

        def _http_fake_send(session, request, **kwargs):
            try:
                return self._http_last_send(session, request, **kwargs)
            except NoMockAddress:
                request = _http_adapter.last_request
                error_msg = 'Connection refused: {0} {1}'.format(
                    request.method,
                    request.url
                )
                response = ConnectionError(error_msg)
                response.request = request
                raise response

        requests.Session.send = _http_fake_send

    def start(self):
        """Overrides default start behaviour by raising ConnectionError instead
        of custom requests_mock.exceptions.NoMockAddress.
        """
        if self._http_last_send is not None:
            raise RuntimeError('HttpMock has already been started')

        # 1) save request.Session.send in self._last_send
        # 2) replace request.Session.send with MockerCore send function
        super(HttpMock, self).start()

        # 3) save MockerCore send function in self._http_last_send
        # 4) replace request.Session.send with HttpMock send function
        self._patch_last_send()

    def stop(self):
        if self._http_last_send is not None:
            # 1) revert request.Session.send to self._http_last_send value
            # 2) reset self._http_last_send
            self._http_last_send = None
            requests.Session.send = self._http_last_send

            # 3) revert request.Session.send to self._last_send value
            # 4) reset self._last_send
            super(HttpMock, self).stop()


_http_mock = HttpMock()

__all__ = []

# expose mocker instance public methods
for __attr in [a for a in dir(_http_mock) if not a.startswith('_')]:
    __all__.append(__attr)
    globals()[__attr] = getattr(_http_mock, __attr)

# expose adapter instance public methods
for __attr in [a for a in dir(_http_adapter) if not a.startswith('_')]:
    __all__.append(__attr)
    globals()[__attr] = getattr(_http_adapter, __attr)
