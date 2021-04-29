# Background logging into file oe other handler support to test libraries
## Overview

Allow store background log events into other sources, such file, sqlite, etc.

Mostly inherited from  [robotbackgroundlogger](https://github.com/robotframework/robotbackgroundlogger)

Difference are:
    
File path provided on logger instance creation cause to log messages into file
    
    import background_custom_logger
    
    current_log = BuiltIn().get_variable_value('${OUTPUT_DIR}')
    logger = background_custom_logger.BackgroundCustomLogger('my_logger', file=os.path.join(current_log, 'log_file.log'))
    
Where:
- first argument Logger thread name inself (Default: BackgroundCustomLogger)
- file  path to file for write logs to

## API extensions

- Module allow assignment of logger handlers
- Best practice to import StreamHandler from 'background_custom_logger'
- Otherwise real thread where from event arrived can be not seen
