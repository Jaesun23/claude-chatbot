from .event_system import Event, EventEmitter, EventSubscriber
from .ui_events import UIEventType, UIEventData

__all__ = [
    'Event',
    'EventEmitter',
    'EventSubscriber',
    'UIEventType',
    'UIEventData'
]

# Version info
__version__ = '0.1.0'
__author__ = 'Your Name'

# Package level logger
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())  # 기본적으로 로깅 비활성화