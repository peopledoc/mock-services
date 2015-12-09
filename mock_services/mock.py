# -*- coding: utf-8 -*-
import logging

import responses


logger = logging.getLogger(__name__)


def is_http_mock_started():
    return hasattr(responses.mock, '_patcher') \
        and hasattr(responses.mock._patcher, 'is_local')


def start_http_mock():
    if not is_http_mock_started():
        responses.start()
        logger.debug('http mock started')
        return True


def stop_http_mock():
    if is_http_mock_started():
        responses.mock._patcher.stop()
        logger.debug('http mock stopped')
        return True
