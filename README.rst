=================
Responses helpers
=================

Aims to provide an easy way to mock an entire service API based on `responses`_
and a simple dict definition of a service. The idea is to mock everything at
start according the definition. Then `responses-helpers`_ permits to
*start/stop* mock locally.

*Note:* rules urls must be regex. They always will be compiled before updating
the main `responses`_ urls registry.

Let's mock our favorite search engine::

    >>> def fake_duckduckgo_cb(request):
    ...     return 200, {}, 'Coincoin!'

    >>> rules = [
    ...     {
    ...         'callback': fake_duckduckgo_cb,
    ...         'content_type': 'text/html',
    ...         'method': 'GET',
    ...         'url': r'^https://duckduckgo.com/\?q='
    ...     },
    ... ]

    >>> from responses_helpers import update_http_rules
    >>> update_http_rules(rules)

    >>> import requests
    >>> requests.get('https://duckduckgo.com/?q=responses').content[:15]
    '<!DOCTYPE html>'

    >>> from responses_helpers import start_http_mock
    >>> start_http_mock()

    >>> requests.get('https://duckduckgo.com/?q=responses').content
    'Coincoin!'


At anytime you can stop the mocking as follow::

    >>> from responses_helpers import stop_http_mock
    >>> stop_http_mock()

    >>> requests.get('https://duckduckgo.com/?q=responses').content[:15]
    '<!DOCTYPE html>'


Or stop mocking during a function call::

    >>> start_http_mock()

    >>> @no_http_mock
    ... def please_do_not_mock_me():
    ...     return requests.get('https://duckduckgo.com/?q=responses').content[:15] == '<!DOCTYPE html>', 'mocked!'

    >>> please_do_not_mock_me


Or start mocking for another function call::

    >>> stop_http_mock()

    >>> @with_http_mock
    ... def please_mock_me():
    ...     assert requests.get('https://duckduckgo.com/?q=responses').content == 'Coincoin', 'no mock!'

    >>> please_mock_me


Have fun in testing external APIs ;)


.. _`responses`: https://github.com/getsentry/responses
.. _`responses-helpers`: https://github.com/novafloss/responses-helpers
