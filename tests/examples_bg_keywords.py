import os
from threading import Thread, Event
from time import sleep
from typing import Dict, AnyStr, Tuple

from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
import background_custom_logger

current_log = BuiltIn().get_variable_value('${OUTPUT_DIR}')
logger = background_custom_logger.BackgroundCustomLogger('my_logger', file=os.path.join(current_log, 'log_file.log'))

_threads: Dict[AnyStr, Tuple[Thread, Event]] = {}


class CustomHandler(background_custom_logger.StreamHandler):
    def emit(self, record):
        record.threadName = record.threadName + "custom_"
        logger.console(f"Custom handler: {record.threadName}")


logger.add_handler(CustomHandler())


def _msg(msg, event: Event):
    logger.info('Start invoked (logger)')
    while not event.isSet():
        logger.info(f"In progress: {msg} (logger)")
        sleep(0.5)
    print('End invoked')


@keyword("Start thread")
def start_thread(name, message):
    _link = logger.get_relative_file_path(BuiltIn().get_variable_value('${OUTPUT_DIR}'))
    logger.warn(f"<a href=\"{_link}\">Bg Log file</a>", html=True)
    _event = Event()
    _thread = Thread(name=name, target=_msg, args=(message, _event), daemon=True)
    _thread.start()
    _threads[name] = _thread, _event
    logger.info(f'Thread {_thread.name} started', also_to_console=True)


@keyword("Stop thread")
def stop_thread(name):
    _thread, _event = _threads.get(name, None)
    if _thread:
        _event.set()
        _thread.join()
    logger.info(f'Thread {_thread.name} stopped', also_to_console=True)
    logger.log_background_messages()


@keyword("Stop logger")
def stop_logger():
    logger.join()
