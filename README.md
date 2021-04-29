# Background logging into file oe other handler support to test libraries
## Overview

Allow store background log events into other sources, such file, sqlite, etc.

Mostly inherited from  [robotbackgroundlogger](https://github.com/robotframework/robotbackgroundlogger)

Difference are:
    
File path provided on logger instance creation cause to log messages into file
    
    import robotbackground_custom_logger
    
    current_log = BuiltIn().get_variable_value('${OUTPUT_DIR}')
    logger = background_custom_logger.BackgroundCustomLogger('my_logger', file=os.path.join(current_log, 'log_file.log'))
    
Where:
- first argument Logger thread name inself (Default: BackgroundCustomLogger)
- file  path to file for write logs to

# Project structure
## Custom Logger

Fro create common logger:

    from robotbackground_custom_logger import logger

For add file handler

    from robotbackground_custom_logger.api import create_file_handler
    current_log = BuiltIn().get_variable_value('${OUTPUT_DIR}')
    fh = create_file_handler(os.path.join(current_log, 'log_file.log')
    logger.add_handler(fh)

## API extensions

For create own handler
    
    from robotbackground_custom_logger.api import StreamHandler
    
    class MyHandler(StreamHandler):
        def emit(record):
            Do something here with record
    
- Module allow assignment of logger handlers
- Best practice to import StreamHandler from 'background_custom_logger'
- Otherwise real thread where from event arrived can be not seen
