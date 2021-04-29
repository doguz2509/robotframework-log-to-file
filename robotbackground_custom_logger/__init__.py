
from .custom_logger import BackgroundCustomLogger
from . import api

__version__ = '1.3.2'

logger = BackgroundCustomLogger()

__all__ = [
    BackgroundCustomLogger.__name__,
    'logger',
    'api'
]
