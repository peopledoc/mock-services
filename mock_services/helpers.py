# -*- coding: utf-8 -*-
import logging

from . import http_mock


logger = logging.getLogger(__name__)


def is_http_mock_started():
    return http_mock.is_started()


def start_http_mock():
    if not http_mock.is_started():
        http_mock.start()
        logger.debug('http mock started')
        return True


def stop_http_mock():
    if http_mock.is_started():
        http_mock.stop()
        logger.debug('http mock stopped')
        return True
