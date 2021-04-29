# Replace emit method for reflect real thread name instead of logging's one
import logging
import logging.handlers
import os

from logging import StreamHandler


def emit(self, record) -> None:
    record.threadName = record.source_thread
    self.orig_emit(record)


StreamHandler.orig_emit = StreamHandler.emit
StreamHandler.emit = emit

DEFAULT_FORMATTER = "%(asctime)s [%(levelname)-8s] [%(threadName)-25s] : %(message)s"

DEFAULT_LOG_COUNT = 10
DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_MAX_BYTES = (1048576 * 5)
DEFAULT_ROLLUP_COUNT = 20


__all__ = ['StreamHandler',
           'DEFAULT_FORMATTER',
           'DEFAULT_LOG_LEVEL',
           'DEFAULT_ROLLUP_COUNT',
           'DEFAULT_LOG_COUNT',
           'DEFAULT_MAX_BYTES']
