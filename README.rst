=============
Mock services
=============

.. image:: https://circleci.com/gh/novafloss/mock-services.svg?style=shield
   :target: https://circleci.com/gh/novafloss/mock-services
   :alt: We are under CI!!

Aims to provide an easy way to mock an entire service API based on
`requests-mock`_ and a simple dict definition of a service. The idea is to mock
everything at start according given rules. Then `mock-services`_ allows to
*start/stop* http mock locally.

During our session we can:

- add rules
- permit external calls
- stop mocking
- reset rules
- restart mocking
- etc.


Mock endpoints explicitly
=========================


*Note:* rules urls must be regex. They always will be compiled before updating
the main `requests-mock`_ urls registry.

Let's mock our favorite search engine::

    >>> def fake_duckduckgo_cb(request):
    ...     return 200, {}, 'Coincoin!'

    >>> rules = [
    ...     {
    ...         'text': fake_duckduckgo_cb,
    ...         'headers': {'Content-Type': 'text/html'},
    ...         'method': 'GET',
    ...         'url': r'^https://duckduckgo.com/\?q='
    ...     },
    ... ]

    >>> from mock_services import update_http_rules
    >>> update_http_rules(rules)

    >>> import requests
    >>> requests.get('https://duckduckgo.com/?q=mock-services').content[:15]
    '<!DOCTYPE html>'

    >>> from mock_services import start_http_mock
    >>> start_http_mock()

    >>> requests.get('https://duckduckgo.com/?q=mock-services').content
    'Coincoin!'


When the http_mock is started if you try to call an external url, it should
fail::

    >>> requests.get('https://www.google.com/#q=mock-services')
    ...
    ConnectionError: Connection refused: GET https://www.google.com/#q=mock-services


Then you can allow external calls if needed::

    >>> from mock_services import http_mock
    >>> http_mock.set_allow_external(True)

    >>> requests.get('https://www.google.com/#q=mock-services').content[:15]
    '<!doctype html>'


At anytime you can stop the mocking as follow::

    >>> from mock_services import stop_http_mock
    >>> stop_http_mock()

    >>> requests.get('https://duckduckgo.com/?q=mock-services').content[:15]
    '<!DOCTYPE html>'


Or stop mocking during a function call::

    >>> start_http_mock()

    >>> @no_http_mock
    ... def please_do_not_mock_me():
    ...     return requests.get('https://duckduckgo.com/?q=mock-services').content[:15] == '<!DOCTYPE html>', 'mocked!'

    >>> please_do_not_mock_me


Or start mocking for another function call::

    >>> stop_http_mock()

    >>> @with_http_mock
    ... def please_mock_me():
    ...     assert requests.get('https://duckduckgo.com/?q=mock-services').content == 'Coincoin', 'no mock!'

    >>> please_mock_me


Mock service easy
=================


You can add REST rules with an explicit method. It will add rules as above and
automatically bind callbacks to fake a REST service.

*Note:* *resource* and *id* regex options are mandatory in the rules urls.

Additionally, `mock_services`_ include `attrs`_ library. It can be use for
field validation as follow.

This service mock will create, get, update and delete resources for you::

    >>> import attr

    >>> rest_rules = [
    ...     {
    ...         'method': 'LIST',
    ...         'url': r'^http://my_fake_service/(?P<resource>api)$'
    ...     },
    ...     {
    ...         'method': 'GET',
    ...         'url': r'^http://my_fake_service/(?P<resource>api)/(?P<id>\d+)$',
    ...     },
    ...     {
    ...         'method': 'GET',
    ...         'url': r'^http://my_fake_service/(?P<resource>api)/(?P<id>\d+)/(?P<action>download)$',
    ...     },
    ...     {
    ...         'method': 'POST',
    ...         'url': r'^http://my_fake_service/(?P<resource>api)$',
    ...         'id_name': 'id',
    ...         'id_factory': int,
    ...         'attrs': {
    ...             'bar': attr.ib(),
    ...             'foo':attr.ib(default=True)
    ...         }
    ...     },
    ...     {
    ...         'method': 'PATCH',
    ...         'url': r'^http://my_fake_service/(?P<resource>api)/(?P<id>\d+)$',
    ...     },
    ...     {
    ...         'method': 'DELETE',
    ...         'url': r'^http://my_fake_service/(?P<resource>api)/(?P<id>\d+)$'
    ...     },
    ... ]

    >>> from mock_services import update_rest_rules
    >>> update_rest_rules(rest_rules)

    >>> from mock_services import start_http_mock
    >>> start_http_mock()

    >>> response = requests.get('http://my_fake_service/api')
    >>> response.status_code
    200
    >>> response.json()
    []

    >>> response = requests.get('http://my_fake_service/api/1')
    >>> response.status_code
    404

    >>> import json

    >>> response = requests.post('http://my_fake_service/api',
    ...                          data=json.dumps({}),
    ...                          headers={'content-type': 'application/json'})
    >>> response.status_code
    400

    >>> response = requests.post('http://my_fake_service/api',
    ...                          data=json.dumps({'bar': 'Python will save the world'}),
    ...                          headers={'content-type': 'application/json'})
    >>> response.status_code
    201
    >>> response.json()
    {
      'id': 1,
      'foo'; True,
      'bar'; 'Python will save the world.'
    }

    >>> response = requests.patch('http://my_fake_service/api/1',
    ...                           data=json.dumps({'bar': "Python will save the world. I don't know how. But it will."}),
    ...                           headers={'content-type': 'application/json'})
    >>> response.status_code
    200

    >>> response = requests.get('http://my_fake_service/api/1')
    >>> response.status_code
    200
    >>> response.json()
    {
      'id': 1,
      'foo'; True,
      'bar'; "Python will save the world. I don't know how. But it will."
    }

    >>> response = requests.delete('http://my_fake_service/api/1')
    >>> response.status_code
    204


More validation
===============


Is some cases you need to validate a resource against another. Then you can add
global validators per endpoint as follow::

    >>> from mock_services import storage
    >>> from mock_services.service import ResourceContext
    >>> from mock_services.exceptions import Http409

    >>> def duplicate_foo(request):
    ...     data = json.loads(request.body)
    ...     ctx = ResourceContext(hostname='my_fake_service', resource='api')
    ...     if data['foo'] in [o['foo'] for o in storage.list(ctx)]:
    ...         raise Http409

    >>> rest_rules_with_validators = [
    ...     {
    ...         'method': 'POST',
    ...         'url': r'^http://my_fake_service/(?P<resource>api)$',
    ...         'validators': [
    ...             duplicate_foo,
    ...         ],
    ...     },
    ... ]

    >>> response = requests.post('http://my_fake_service/api',
    ...                          data=json.dumps({'foo': 'bar'}),
    ...                          headers={'content-type': 'application/json'})
    >>> response.status_code
    201

    >>> response = requests.post('http://my_fake_service/api',
    ...                          data=json.dumps({'foo': 'bar'}),
    ...                          headers={'content-type': 'application/json'})
    >>> response.status_code
    409


Have fun in testing external APIs ;)


.. _`attrs`: https://github.com/hynek/attrs
.. _`requests-mock`: https://github.com/openstack/requests-mock
.. _`mock-services`: https://github.com/novafloss/mock-services
