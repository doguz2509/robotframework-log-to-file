import os
from datetime import datetime
from threading import Thread, Event
from time import sleep
from typing import Dict, AnyStr, Tuple
import logging.handlers

from threading import currentThread

from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from robotbackground_custom_logger import logger as my_logger
from robotbackground_custom_logger.api import *
from robotbackground_custom_logger.api import DEFAULT_MAX_BYTES

current_log = BuiltIn().get_variable_value('${OUTPUT_DIR}')
current_level = BuiltIn().get_variable_value('${LOG_LEVEL}')

file_handler = logging.handlers.RotatingFileHandler(os.path.join(current_log, 'log_file.log'),
                                                    maxBytes=DEFAULT_MAX_BYTES,
                                                    backupCount=DEFAULT_ROLLUP_COUNT)

my_logger.add_handler(file_handler)
my_logger.set_level(current_level)
_threads: Dict[AnyStr, Tuple[Thread, Event]] = {}


class CustomHandler(StreamHandler):
    def emit(self, record):
        record.threadName = record.threadName + "custom_"
        my_logger.console(f"Custom handler: {record.threadName}")


def _msg(msg, event: Event):
    my_logger.info('Start invoked (logger)')
    while not event.isSet():
        my_logger.info(f"TS: {datetime.now()} - In progress: {msg} (info) {currentThread().getName()}")
        my_logger.warn(f"TS: {datetime.now()} - In progress: {msg} (warn) {currentThread().getName()}")
        my_logger.debug(f"TS: {datetime.now()} - In progress: {msg} (debug) {currentThread().getName()}")
        my_logger.trace(f"TS: {datetime.now()} - In progress: {msg} (trace) {currentThread().getName()}")
        my_logger.error(f"TS: {datetime.now()} - In progress: {msg} (error) {currentThread().getName()}")
        sleep(0.5)
    print('End invoked')


@keyword("Start thread")
def start_thread(name):
    _link = os.path.relpath(file_handler.baseFilename, current_log)
    my_logger.warn(f"<a href=\"{_link}\">Bg Log file</a>", html=True)
    _event = Event()
    message = name + ' ' + BuiltIn().get_variable_value('${TEST_NAME}')
    _thread = Thread(name=name, target=_msg, args=(message, _event), daemon=True)
    _thread.start()
    _threads[name] = _thread, _event
    my_logger.debug(f'Thread {_thread.name} started')


@keyword("Stop thread")
def stop_thread(name):
    _thread, _event = _threads.get(name, None)
    if _thread:
        _event.set()
        _thread.join()
        my_logger.info(f'Thread {_thread.name} stopped', also_to_console=True)
        # my_logger.reset_background_messages(_thread.name)


@keyword("Stop all")
def stop_all():
    for n, (t, e) in _threads.items():
        e.set()
        t.join()
        my_logger.info(f"Thread {n} stopped")
        # my_logger.reset_background_messages(n)


@keyword("Stop logger")
def stop_logger():
    my_logger.console("\nStop logger\n")
    my_logger.join()
