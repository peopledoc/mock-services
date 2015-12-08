import logging
import unittest

import requests

import responses

from responses_helpers import is_http_mock_started
from responses_helpers import no_http_mock
from responses_helpers import start_http_mock
from responses_helpers import stop_http_mock
from responses_helpers import update_http_rules
from responses_helpers import with_http_mock


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)-8s %(name)s  %(message)s'
)


def fake_duckduckgo_cb(request):
    return 200, {}, 'Coincoin!'


rules = [
    {
        'callback': fake_duckduckgo_cb,
        'content_type': 'text/html',
        'method': 'GET',
        'url': r'^https://duckduckgo.com/\?q='
    },
]


class ResponsesHelpersTestCase(unittest.TestCase):

    def setUp(self):
        stop_http_mock()
        responses.reset()

    tearDown = setUp

    def test_update_rules(self):

        self.assertFalse(responses._default_mock._urls)

        # add first rule
        update_http_rules(rules)

        self.assertEqual(len(responses._default_mock._urls), 1)
        self.assertEqual(sorted(responses._default_mock._urls[0].keys()), [
            'callback',
            'content_type',
            'match_querystring',
            'method',
            'url',
        ])

        self.assertTrue(hasattr(responses._default_mock._urls[0]['url'], 'match'))                             # noqa
        self.assertTrue(responses._default_mock._urls[0]['url'].match('https://duckduckgo.com/?q=responses'))  # noqa

        self.assertTrue(hasattr(responses._default_mock._urls[0]['callback'], '__call__'))                     # noqa

        self.assertEqual(responses._default_mock._urls[0]['match_querystring'], True)                          # noqa
        self.assertEqual(responses._default_mock._urls[0]['method'], 'GET')
        self.assertEqual(responses._default_mock._urls[0]['content_type'], 'text/html')                        # noqa

        # add second rule
        update_http_rules([
            {
                'body': '{"coin": 1}',
                'method': 'POST',
                'status': 201,
                'url': r'http://dummy/',
            },
        ])

        self.assertEqual(len(responses._default_mock._urls), 2)
        self.assertEqual(sorted(responses._default_mock._urls[1].keys()), [
            'adding_headers',
            'body',
            'content_type',
            'match_querystring',
            'method',
            'status',
            'stream',
            'url',
        ])

        self.assertEqual(responses._default_mock._urls[1]['adding_headers'], None)       # noqa
        self.assertEqual(responses._default_mock._urls[1]['body'], '{"coin": 1}')       # noqa
        self.assertEqual(responses._default_mock._urls[1]['content_type'], 'application/json')       # noqa
        self.assertEqual(responses._default_mock._urls[1]['match_querystring'], True)       # noqa
        self.assertEqual(responses._default_mock._urls[1]['method'], 'POST')       # noqa
        self.assertEqual(responses._default_mock._urls[1]['status'], 201)       # noqa
        self.assertEqual(responses._default_mock._urls[1]['stream'], False)       # noqa

        self.assertTrue(hasattr(responses._default_mock._urls[1]['url'], 'match'))          # noqa
        self.assertTrue(responses._default_mock._urls[1]['url'].match('http://dummy/'))  # noqa

    def test_start_http_mock(self):

        update_http_rules(rules)

        response = requests.get('https://duckduckgo.com/?q=responses')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content[:15], '<!DOCTYPE html>')

        self.assertTrue(start_http_mock())

        response = requests.get('https://duckduckgo.com/?q=responses')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Coincoin!')

    def test_stop_http_mock(self):

        update_http_rules(rules)

        self.assertTrue(start_http_mock())

        response = requests.get('https://duckduckgo.com/?q=responses')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Coincoin!')

        self.assertTrue(stop_http_mock())

        response = requests.get('https://duckduckgo.com/?q=responses')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content[:15], '<!DOCTYPE html>')

    def test_restart_http_mock(self):

        update_http_rules(rules)

        start_http_mock()

        response = requests.get('https://duckduckgo.com/?q=responses')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Coincoin!')

        self.assertTrue(stop_http_mock())

        # already stopped
        self.assertFalse(stop_http_mock())

        response = requests.get('https://duckduckgo.com/?q=responses')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content[:15], '<!DOCTYPE html>')

        self.assertTrue(start_http_mock())

        response = requests.get('https://duckduckgo.com/?q=responses')
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

            response = requests.get('https://duckduckgo.com/?q=responses')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content[:15], '<!DOCTYPE html>')

        self.assertTrue(is_http_mock_started())

    def test_with_http_mock(self):

        update_http_rules(rules)

        self.assertFalse(is_http_mock_started())

        @with_http_mock
        def please_do_not_mock_me():

            self.assertTrue(is_http_mock_started())

            response = requests.get('https://duckduckgo.com/?q=responses')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, 'Coincoin!')

        self.assertFalse(is_http_mock_started())
