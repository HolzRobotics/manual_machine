import logging
import os

from logstash import TCPLogstashHandler
from dotenv import dotenv_values, load_dotenv

load_dotenv('.env')

PROJECT_NAME = os.getenv("PROJECT_NAME", "UNKNOWN")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOGSTASH_HOST = os.getenv("LOGSTASH_HOST")
LOGSTASH_PORT = int(os.getenv("LOGSTASH_PORT"))

_logger = logging.getLogger("manual_machine")
_logger.setLevel(LOG_LEVEL)


# Add a StreamHandler for Docker logs
stream_handler = logging.StreamHandler()
stream_handler.setLevel(LOG_LEVEL)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)

_logger.addHandler(stream_handler)


if LOGSTASH_HOST and LOGSTASH_PORT:
    _logger.addHandler(TCPLogstashHandler(
        LOGSTASH_HOST,
        LOGSTASH_PORT,
        version=1,
    ))
else:
    _logger.warning("Logstash variables not found, start with StreamHandler only")


class HolzLogger:
    def __init__(self, _logger):
        self._logger = _logger

    @staticmethod
    def _extend_kwargs(**kwargs):
        if 'extra' in kwargs:
            kwargs['extra']['project'] = PROJECT_NAME
        else:
            kwargs['extra'] = {'project': PROJECT_NAME}

        return kwargs

    def _log(self, level, msg, *args, **kwargs):
        kwargs = self._extend_kwargs(**kwargs)
        self._logger.log(level, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, **kwargs)

    def exception(self, exc, *args, **kwargs):
        kwargs = self._extend_kwargs(**kwargs)
        self._logger.exception(exc, *args, **kwargs)


logger = HolzLogger(_logger)
