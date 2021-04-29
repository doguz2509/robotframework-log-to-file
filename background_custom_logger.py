import logging
import logging.handlers
from logging import StreamHandler
import os
from threading import currentThread, Thread, RLock, Event
from time import sleep

from robot.api import logger
from robot.utils.robottime import timestr_to_secs
from robotbackgroundlogger import BackgroundLogger, BackgroundMessage as orig_bg_message

__version__ = '1.2.1'

DEFAULT_FORMATTER = "%(asctime)s [%(levelname)-8s] [%(threadName)-14s] : %(message)s"
DEFAULT_LOG_INTERVAL = '5s'
DEFAULT_LOG_COUNT = 10


# Replace emit method for reflect real thread name instead of loggin's one
def emit(self, record: logging.LogRecord) -> None:
    record.threadName = record.source_thread
    self.orig_emit(record)


StreamHandler.orig_emit = StreamHandler.emit
StreamHandler.emit = emit


def robot_level_index(level):
    return {'TRACE': logging.DEBUG,
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'HTML': logging.INFO,
            'WARN': logging.WARN,
            'ERROR': logging.ERROR}[level]


def create_file_handler(file_path, max_bytes=(1048576 * 5), rollup_count=20, cumulative=False) -> logging.Handler:
    path, file_name = os.path.split(file_path)
    if not os.path.exists(path):
        os.makedirs(path)
    elif not cumulative:
        if os.path.exists(file_path):
            os.remove(file_path)
    handler = logging.handlers.RotatingFileHandler(file_path, maxBytes=max_bytes, backupCount=rollup_count)
    return handler


class QueueList(list):
    def __init__(self, lock=RLock()):
        self._lock = lock

    def append(self, item) -> None:
        with self._lock:
            super().append(item)

    def extend(self, items=None, *args):
        items = items or []
        for i in items + list(args):
            self.append(i)

    def pop(self, index=0):
        with self._lock:
            return super().pop(index)

    def get_items(self, **filters):
        for item in self:
            for attr, value in filters.items():
                if not hasattr(item, attr):
                    continue
                if getattr(item, attr) != value:
                    continue
            yield item

    def clear(self) -> None:
        with self._lock:
            super().clear()

    def put(self, item):
        self.append(item)

    def get(self):
        with self._lock:
            self.pop(0)


class BackgroundMessage(orig_bg_message):

    def __init__(self, message, level='INFO', html=False, thread=None):
        super().__init__(message, level, html)
        self.thread = thread or currentThread().getName()

    def format(self):
        # Can support HTML logging only with INFO level.
        html = self.html and self.level == 'INFO'
        level = self.level if not html else 'HTML'
        return self.message


def create_default_handler():
    handler = logging.StreamHandler()
    return handler


class BackgroundCustomLogger(BackgroundLogger, Thread):
    def __init__(self, name=None, log_count=DEFAULT_LOG_COUNT,
                 file=None, formatter=DEFAULT_FORMATTER, log_interval=DEFAULT_LOG_INTERVAL):
        """
        BackgroundCustomLogger instance

        :param name: Thread name to be logged
        :param log_count: count of messages logging to file at once (avoid thread starvation messages stream are load)
        :param file: log file name (Optional; nothing will be logged if omitted)
        :param formatter: log format (Optional)
        :param log_interval: time interval (Optional)
        """
        BackgroundLogger.__init__(self)
        self._messages = QueueList(self.lock)
        self._interval = timestr_to_secs(log_interval)
        self._log_count = log_count
        self._formatter = formatter
        self._event = Event()
        self._is_started_once = False
        Thread.__init__(self, name=name or self.__class__.__name__, daemon=True)
        self._logging = logging.getLogger(self.name)
        self._log_file = file
        if file:
            file_handler = create_file_handler(file)
            self.add_handler(file_handler)
        else:
            self.add_handler(create_default_handler())
        logger.info(f"{self.name} created")

    def get_relative_file_path(self, start_from):
        if self._log_file:
            return os.path.relpath(self._log_file, start_from)
        return ''

    @property
    def formatter(self) -> logging.Formatter:
        return logging.Formatter(self._formatter)

    def add_handler(self, handler: logging.Handler):
        handler.setFormatter(self.formatter)
        self._logging.addHandler(handler)

    def run(self):
        while not self._event.isSet():
            if len(self._messages) >= 0:
                self.log_background_messages()
            sleep(self._interval)

    def join(self, timeout=None):
        self._event.set()
        super().join(timeout)
        logger.info(f"{self.name} stopped", also_console=True)

    def write(self, msg, level, html=False):
        if not self._is_started_once:
            logger.info(f"{self.name} starting")
            self.start()
            self._is_started_once = True

        with self.lock:
            thread = currentThread().getName()
            if thread in self.LOGGING_THREADS:
                logger.write(msg, level, html)
            else:
                message = BackgroundMessage(msg, level, html, thread)
                self._messages.put(message)

    def log_background_messages(self, name=None):
        """Forwards messages logged on background to Robot Framework log.

        By default forwards all messages logged by all threads, but can be
        limited to a certain thread by passing thread's name as an argument.
        Logged messages are removed from the message storage.

        This method must be called from the main thread.
        """
        thread = currentThread().getName()
        if thread not in self.LOGGING_THREADS:
            counter = self._log_count
            self._logging.log(robot_level_index('DEBUG'),
                              f"Bg Logger iteration started for {counter} items",
                              extra={'source_thread': self.name})
            while True:
                try:
                    assert counter > 0
                    message = self._messages.pop()
                    _level = message.level if message.level != 'TRACE' else 'DEBUG'
                    _level_index = robot_level_index(_level)
                    self._logging.log(_level_index, message.format(), extra={'source_thread': message.thread})
                except (IndexError, AssertionError):
                    break
                else:
                    counter -= 1
            self._logging.log(robot_level_index('DEBUG'),
                              f"Bg Logger iteration ended (Treated {self._log_count - counter} items)",
                              extra={'source_thread': self.name})
        with self.lock:
            if name:
                for message in self._messages.get_items(thread=thread):
                    print(message.format())
            else:
                while len(self._messages) > 0:
                    message = self._messages.pop()
                    print(message.format())

    def reset_background_messages(self, name=None):
        self._messages.clear()


__all__ = [
    'BackgroundCustomLogger',
    'StreamHandler'
]
