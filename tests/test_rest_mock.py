import json
import logging
import unittest
import uuid

from functools import partial

import attr

import requests

from mock_services import reset_rules
from mock_services import start_http_mock
from mock_services import stop_http_mock
from mock_services import update_rest_rules
from mock_services import http_mock
from mock_services import storage
from mock_services.exceptions import Http400
from mock_services.exceptions import Http409
from mock_services.service import ResourceContext


CONTENTTYPE_JSON = {'Content-Type': 'application/json'}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(name)s  %(message)s'
)

rest_rules = [
    {
        'method': 'LIST',
        'url': r'^http://my_fake_service/(?P<resource>api)$'
    },
    {
        'method': 'HEAD',
        'url': r'^http://my_fake_service/(?P<resource>api)/(?P<id>\d+)$',
    },
    {
        'method': 'GET',
        'url': r'^http://my_fake_service/(?P<resource>api)/(?P<id>\d+)$',
    },
    {
        'method': 'GET',
        'url': r'^http://my_fake_service/(?P<resource>api)/(?P<id>\d+)/(?P<action>download)$',  # noqa
    },
    {
        'method': 'POST',
        'url': r'^http://my_fake_service/(?P<resource>api)$',
        'id_name': 'id',
        'id_factory': int,
        'attrs': {
            'bar': attr.ib()
        }
    },
    {
        'method': 'PATCH',
        'url': r'^http://my_fake_service/(?P<resource>api)/(?P<id>\d+)$',
    },
    {
        'method': 'PUT',
        'url': r'^http://my_fake_service/(?P<resource>api)/(?P<id>\d+)$',
        'attrs': {
            'foo': attr.ib(),
            'bar': attr.ib()
        }
    },
    {
        'method': 'DELETE',
        'url': r'^http://my_fake_service/(?P<resource>api)/(?P<id>\d+)$'
    },
    {
        'method': 'GET',
        'url': r'^http://my_fake_service/(?P<resource>api/v2)/(?P<id>\w+-\w+-\w+-\w+-\w+)$',  # noqa
    },
    {
        'method': 'POST',
        'url': r'^http://my_fake_service/(?P<resource>api/v2)$',
        'id_name': 'uuid',
        'id_factory': uuid.UUID,
    },
]


def should_have_foo(request):
    data = json.loads(request.body)
    if 'foo' not in data:
        raise Http400


def duplicate_foo(request):
    data = json.loads(request.body)
    ctx = ResourceContext(hostname='my_fake_service', resource='api')
    if data['foo'] in [o['foo'] for o in storage.list(ctx)]:
        raise Http409


rest_rules_with_validators = [
    {
        'method': 'POST',
        'url': r'^http://my_fake_service/(?P<resource>api)$',
        'validators': [
            should_have_foo,
            duplicate_foo,
        ],
    },
]


class RestTestCase(unittest.TestCase):

    def setUp(self):
        stop_http_mock()
        reset_rules()

    tearDown = setUp

    def _test_rule(self, index, method, url_to_match,
                   content_type='application/json'):

        matcher = http_mock.get_rules()[index]

        self.assertEqual(matcher._method, method)

        self.assertTrue(hasattr(matcher._url, 'match'))
        self.assertTrue(matcher._url.match(url_to_match))

        response = matcher._responses[0]
        self.assertTrue(hasattr(response._params['text'], '__call__'))
        self.assertEqual(response._params['headers']['Content-Type'], content_type)  # noqa

    def test_update_rules(self):

        self.assertFalse(http_mock.get_rules())

        update_rest_rules(rest_rules)

        self.assertEqual(len(http_mock.get_rules()), 10)

        self._test_rule(0, 'GET', 'http://my_fake_service/api')
        self._test_rule(1, 'HEAD', 'http://my_fake_service/api/1',
                        content_type='text/plain')
        self._test_rule(2, 'GET', 'http://my_fake_service/api/1')
        self._test_rule(3, 'GET', 'http://my_fake_service/api/1/download')
        self._test_rule(4, 'POST', 'http://my_fake_service/api')
        self._test_rule(5, 'PATCH', 'http://my_fake_service/api/1')
        self._test_rule(6, 'PUT', 'http://my_fake_service/api/1')
        self._test_rule(7, 'DELETE', 'http://my_fake_service/api/1',
                        content_type='text/plain')
        self._test_rule(8, 'GET', 'http://my_fake_service/api/v2/{0}'.format(uuid.uuid4()))  # noqa
        self._test_rule(9, 'POST', 'http://my_fake_service/api/v2')

    def test_update_rules_invalid_method(self):
        update_func = partial(update_rest_rules, [
            {
                'text': '',
                'method': 'INVALID',
                'status_code': 200,
                'url': r'^https://invalid_method.com/'
            }
        ])
        self.assertRaises(NotImplementedError, update_func,
                          'invalid method "INVALID" for: ^https://invalid_method.com/')  # noqa

    def test_rest_mock(self):

        url = 'http://my_fake_service/api'

        update_rest_rules(rest_rules)
        self.assertTrue(start_http_mock())

        r = requests.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers, {'content-type': 'application/json'})
        self.assertEqual(r.json(), [])

        r = requests.get(url + '/1')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.headers, {'content-type': 'application/json'})
        self.assertEqual(r.json(), {'error': 'Not Found'})

        r = requests.get(url + '/1/download')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.headers, {'content-type': 'application/json'})
        self.assertEqual(r.json(), {'error': 'Not Found'})

        r = requests.post(url, data=json.dumps({}), headers=CONTENTTYPE_JSON)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.headers, {'content-type': 'application/json'})
        self.assertEqual(r.json(), {'error': 'Bad Request'})

        r = requests.patch(url + '/1', data=json.dumps({}))
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.headers, {'content-type': 'application/json'})
        self.assertEqual(r.json(), {'error': 'Not Found'})

        r = requests.delete(url + '/1')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.headers, {'content-type': 'text/plain'})
        self.assertEqual(r.content, 'Not Found')

        # add some data

        r = requests.post(url, data=json.dumps({
            'foo': True,
            'bar': 'Python will save the world.',
        }), headers=CONTENTTYPE_JSON)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.headers, {'content-type': 'application/json'})
        self.assertEqual(r.json(), {
            'id': 1,
            'foo': True,
            'bar': 'Python will save the world.',
        })

        r = requests.head(url + '/1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers, {
            'content-type': 'text/plain',
            'id': '1',
        })
        self.assertEqual(r.content, '')

        # recheck list get ...

        r = requests.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers, {'content-type': 'application/json'})
        self.assertEqual(r.json(), [
            {
                'id': 1,
                'foo': True,
                'bar': 'Python will save the world.',
            }
        ])

        r = requests.patch(url + '/1', data=json.dumps({
            'bar': "Python will save the world. I don't know how. But it will."
        }))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers, {'content-type': 'application/json'})
        self.assertEqual(r.json(), {
            'id': 1,
            'foo': True,
            'bar': "Python will save the world. I don't know how. But it will.",  # noqa
        })

        # missing foo field -> 400
        r = requests.put(url + '/1', data=json.dumps({
            'bar': "Python will save the world. I don't know how. But it will."
        }))
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.headers, {'content-type': 'application/json'})
        self.assertEqual(r.json(), {'error': 'Bad Request'})

        r = requests.put(url + '/1', data=json.dumps({
            'foo': False,
            'bar': "Python will save the world. I don't know how. But it will."
        }))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers, {'content-type': 'application/json'})
        self.assertEqual(r.json(), {
            'id': 1,
            'foo': False,
            'bar': "Python will save the world. I don't know how. But it will.",  # noqa
        })

        r = requests.get(url + '/1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers, {'content-type': 'application/json'})
        self.assertEqual(r.json(), {
            'id': 1,
            'foo': False,
            'bar': "Python will save the world. I don't know how. But it will.",  # noqa
        })

        r = requests.delete(url + '/1')
        self.assertEqual(r.status_code, 204)
        self.assertEqual(r.headers, {'content-type': 'text/plain'})
        self.assertEqual(r.content, '')

        r = requests.get(url + '/1')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.headers, {'content-type': 'application/json'})
        self.assertEqual(r.json(), {
            'error': 'Not Found'
        })

    def test_rest_mock_with_uuid(self):

        url = 'http://my_fake_service/api/v2'

        update_rest_rules(rest_rules)
        self.assertTrue(start_http_mock())

        r = requests.get(url + '/{0}'.format(uuid.uuid4()))
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.headers, {'content-type': 'application/json'})
        self.assertEqual(r.json(), {'error': 'Not Found'})

        r = requests.post(url, data=json.dumps({'foo': 'bar'}),
                          headers=CONTENTTYPE_JSON)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.headers, {'content-type': 'application/json'})

        data = r.json()
        _uuid = data.get('uuid')
        self.assertTrue(uuid.UUID(_uuid))
        self.assertEqual(data, {
            'uuid': _uuid,
            'foo': 'bar',
        })

        r = requests.get(url + '/' + _uuid)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers, {'content-type': 'application/json'})
        self.assertEqual(r.json(), {
            'uuid': _uuid,
            'foo': 'bar',
        })

    def test_validators(self):

        url = 'http://my_fake_service/api'

        update_rest_rules(rest_rules_with_validators)
        self.assertTrue(start_http_mock())

        r = requests.post(url, data=json.dumps({}), headers=CONTENTTYPE_JSON)
        self.assertEqual(r.status_code, 400)

        r = requests.post(url, data=json.dumps({
            'foo': 'bar',
        }), headers=CONTENTTYPE_JSON)
        self.assertEqual(r.status_code, 201)

        r = requests.post(url, data=json.dumps({
            'foo': 'bar',
        }), headers=CONTENTTYPE_JSON)
        self.assertEqual(r.status_code, 409)

    def test_update_rules_with_another_body_arg(self):

        update_rest_rules([
            {
                'content': 'Coincoin Content!',
                'method': 'GET',
                'url': r'^http://my_fake_service',
            }
        ])
        self.assertTrue(start_http_mock())

        r = requests.get('http://my_fake_service')
        self.assertEqual(r.content, 'Coincoin Content!')
