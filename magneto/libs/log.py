# coding: utf-8

import logging

from .colorlog import ColorizingStreamHandler


logging.StreamHandler = ColorizingStreamHandler
logging.BASIC_FORMAT = "%(asctime)s [%(name)s] %(message)s"
logging.basicConfig(level=logging.INFO)


def get_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger
