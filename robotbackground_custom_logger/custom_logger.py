import logging
import logging.handlers
from datetime import datetime
from threading import currentThread, Thread, RLock, Event
from time import sleep

from robot.api import logger
from robot.utils import is_truthy
from robotbackgroundlogger import BackgroundLogger, BackgroundMessage as orig_bg_message

from . import api


def performance_tuner(event_count: int):
    if 0 <= event_count <= 20:
        return 3
    if 20 < event_count <= 100:
        return 1
    if 100 < event_count <= 500:
        return 0.2
    if 500 < event_count <= 1000:
        return 0.05
    return 0.02


def robot_level_index(level):
    return {'TRACE': logging.DEBUG // 2,
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'HTML': logging.INFO,
            'WARN': logging.WARN,
            'ERROR': logging.ERROR}[level]


def _checkLevel(logger_level, msg_level):
    try:
        assert logger_level <= robot_level_index(msg_level)
    except AssertionError:
        return False
    else:
        return True


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
        return self.message

    def __str__(self):
        return super().format()


class BackgroundCustomLogger(BackgroundLogger, Thread):
    def __init__(self, name=None):
        """
        BackgroundCustomLogger instance

        :param name: Thread name to be logged
        """
        BackgroundLogger.__init__(self)
        Thread.__init__(self, name=name or self.__class__.__name__, target=self._run, daemon=True)
        self._messages = QueueList(self.lock)
        self._interval = performance_tuner(0)
        self._log_count = api.DEFAULT_LOG_COUNT
        self._formatter = api.DEFAULT_FORMATTER
        self._event = Event()
        self._is_started_once = False

        self._logging = None
        self._level = robot_level_index(api.DEFAULT_LOG_LEVEL)
        self._get_logger()
        self._log_file = None

        self.add_handler(api.StreamHandler())
        logger.info(f"{self.name} created")

    # Private methods
    def _get_logger(self):
        self._logging = logging.getLogger(self.name)

    @property
    def pooled_till_now(self):
        return len(self._messages)

    def _tune_performance(self, enforce_count=None):
        self._interval = performance_tuner(enforce_count or self.pooled_till_now)

    def _run(self):
        while not self._event.isSet() or self.pooled_till_now > 0:
            if self.pooled_till_now >= 0:
                # if currentThread().getName() not in self.LOGGING_THREADS:
                self.log_background_messages()
                # else:
                #     self.reset_background_messages()
                self._tune_performance(1001 if self._event.isSet() else None)
            sleep(self._interval)

    # Public methods
    @property
    def formatter(self) -> logging.Formatter:
        return logging.Formatter(self._formatter)

    def set_level(self, level):
        self._level = robot_level_index(level)

    def add_handler(self, handler: logging.Handler):
        handler.setFormatter(self.formatter)
        self._logging.addHandler(handler)

    def join(self, timeout=None):
        self._event.set()
        super().join(timeout)
        logger.info(f"{self.name} stopped", also_console=True)

    def write(self, msg, level, html=False):
        try:
            assert _checkLevel(self._level, level)
            self._tune_performance(0)
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

        except AssertionError:
            pass

    def log_background_messages(self, name=None):
        """Forwards messages logged on background to Robot Framework log.

        By default forwards all messages logged by all threads, but can be
        limited to a certain thread by passing thread's name as an argument.
        Logged messages are removed from the message storage.

        This method must be called from the main thread.
        """
        counter = self._log_count
        while True:
            try:
                assert counter > 0
                message = self._messages.pop()
                _level = message.level if message.level != 'TRACE' else 'DEBUG'
                _level_index = robot_level_index(_level if _level != 'TRACE' else 'DEBUG')
                self._logging.log(_level_index, message.format(), extra={'source_thread': message.thread})
            except (IndexError, AssertionError):
                break
            else:
                counter -= 1

    def reset_background_messages(self, name=None):
        logger.info(f"Remain messages for -> {f'thread {name}' if name else 'all threads'}")
        if name:
            assert currentThread().getName() in self.LOGGING_THREADS, f"Cannot reset messages from thread {name}"
            thread_messages = list(self._messages.get_items(thread=name))
            while len(thread_messages) > 0:
                message = thread_messages.pop()
                logger.write(f"{message}", message.level, message.html)
        else:
            while self.pooled_till_now > 0:
                message = self._messages.pop()
                logger.write(f"{message}", message.level, message.html)

    def info(self, msg, **kwargs):
        html = kwargs.get('html', None)
        console = kwargs.get('console', None) or kwargs.get('also_to_console', None) or kwargs.get('also_console', None)
        console = is_truthy(console)
        super().info(msg, html=html, also_to_console=console)
