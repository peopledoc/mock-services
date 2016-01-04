import logging
import unittest

import requests

from requests.exceptions import ConnectionError

from mock_services import http_mock
from mock_services import is_http_mock_started
from mock_services import no_http_mock
from mock_services import reset_rules
from mock_services import start_http_mock
from mock_services import stop_http_mock
from mock_services import update_http_rules
from mock_services import with_http_mock


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(name)s  %(message)s'
)


def fake_duckduckgo_cb(request, context):
    return 'Coincoin!'


rules = [
    {
        'text': fake_duckduckgo_cb,
        'headers': {'Content-Type': 'text/html'},
        'method': 'GET',
        'url': r'^https://duckduckgo.com/\?q='
    },
]


class HttpTestCase(unittest.TestCase):

    def setUp(self):
        stop_http_mock()
        reset_rules()
        http_mock.set_allow_external(False)

    tearDown = setUp

    def test_reset_rules(self):

        self.assertFalse(http_mock.get_rules())

        update_http_rules(rules)
        self.assertEqual(len(http_mock.get_rules()), 1)

        # reset
        reset_rules()
        self.assertFalse(http_mock.get_rules())

    def test_update_rules(self):

        self.assertFalse(http_mock.get_rules())

        # add first rule
        update_http_rules(rules)

        self.assertEqual(len(http_mock.get_rules()), 1)

        matcher = http_mock.get_rules()[0]
        self.assertEqual(matcher._method, 'GET')
        self.assertTrue(hasattr(matcher._url, 'match'))
        self.assertTrue(matcher._url.match('https://duckduckgo.com/?q=mock-services'))  # noqa

        response = matcher._responses[0]
        self.assertTrue(hasattr(response._params['text'], '__call__'))
        self.assertEqual(response._params['headers']['Content-Type'], 'text/html')  # noqa

        # add second rule
        update_http_rules([
            {
                'method': 'POST',
                'status_code': 201,
                'text': '{"coin": 1}',
                'url': r'http://dummy/',
            },
        ])

        self.assertEqual(len(http_mock.get_rules()), 2)

        matcher = http_mock.get_rules()[1]
        self.assertTrue(hasattr(matcher._url, 'match'))
        self.assertTrue(matcher._url.match('http://dummy/'))
        self.assertEqual(matcher._method, 'POST')

        response = matcher._responses[0]
        self.assertEqual(response._params['status_code'], 201)
        self.assertEqual(response._params['text'], '{"coin": 1}')
        self.assertEqual(response._params['headers']['Content-Type'], 'text/plain')  # noqa

    def test_start_http_mock(self):

        update_http_rules(rules)

        response = requests.get('https://duckduckgo.com/?q=mock-services')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content[:15], '<!DOCTYPE html>')

        self.assertTrue(start_http_mock())

        response = requests.get('https://duckduckgo.com/?q=mock-services')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Coincoin!')

    def test_stop_http_mock(self):

        update_http_rules(rules)

        self.assertTrue(start_http_mock())

        response = requests.get('https://duckduckgo.com/?q=mock-services')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Coincoin!')

        self.assertTrue(stop_http_mock())

        response = requests.get('https://duckduckgo.com/?q=mock-services')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content[:15], '<!DOCTYPE html>')

    def test_restart_http_mock(self):

        update_http_rules(rules)

        start_http_mock()

        response = requests.get('https://duckduckgo.com/?q=mock-services')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Coincoin!')

        self.assertTrue(stop_http_mock())

        # already stopped
        self.assertFalse(stop_http_mock())

        response = requests.get('https://duckduckgo.com/?q=mock-services')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content[:15], '<!DOCTYPE html>')

        self.assertTrue(start_http_mock())

        response = requests.get('https://duckduckgo.com/?q=mock-services')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Coincoin!')

        # already started
        self.assertFalse(start_http_mock())

    def test_is_http_mock_started(self):

        update_http_rules(rules)

        self.assertFalse(is_http_mock_started())
        self.assertTrue(start_http_mock())
        self.assertTrue(is_http_mock_started())

    def test_no_http_mock(self):

        update_http_rules(rules)

        self.assertTrue(start_http_mock())

        @no_http_mock
        def please_do_not_mock_me():

            self.assertFalse(is_http_mock_started())

            response = requests.get('https://duckduckgo.com/?q=mock-services')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content[:15], '<!DOCTYPE html>')

        self.assertTrue(is_http_mock_started())

    def test_with_http_mock(self):

        update_http_rules(rules)

        self.assertFalse(is_http_mock_started())

        @with_http_mock
        def please_do_not_mock_me():

            self.assertTrue(is_http_mock_started())

            response = requests.get('https://duckduckgo.com/?q=mock-services')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, 'Coincoin!')

        self.assertFalse(is_http_mock_started())

    def test_real_http_0(self):

        update_http_rules(rules)

        self.assertTrue(start_http_mock())

        # mocked
        response = requests.get('https://duckduckgo.com/?q=mock-services')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Coincoin!')

        # not mocked but fail
        self.assertRaises(ConnectionError, requests.get,
                          'https://www.google.com/#q=mock-services')
        # test we keep the request
        try:
            url = 'https://www.google.com/#q=mock-services'
            requests.get(url)
        except ConnectionError as e:
            self.assertEqual(e.request.url, url)

    def test_real_http_1(self):

        update_http_rules(rules)
        self.assertTrue(start_http_mock())

        # allow external call
        http_mock.set_allow_external(True)

        # mocked
        response = requests.get('https://duckduckgo.com/?q=mock-services')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Coincoin!')

        # not mocked but do an external call
        response = requests.get('https://www.google.com/#q=mock-services')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content[:15], '<!doctype html>')
