from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """이벤트 데이터를 담는 클래스"""
    type: str
    data: Any = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class EventSubscriber:
    """이벤트 구독자 메타데이터"""
    def __init__(self, callback: Callable, priority: int = 0):
        self.callback = callback
        self.priority = priority
        self.created_at = datetime.now()

class EventEmitter:
    """이벤트 관리 및 처리를 담당하는 클래스"""
    
    def __init__(self):
        self._listeners: Dict[str, List[EventSubscriber]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        logger.info("EventEmitter initialized")
        
    def on(self, event_type: str, callback: Callable, priority: int = 0) -> None:
        """
        이벤트 리스너 등록
        
        Args:
            event_type: 구독할 이벤트 타입
            callback: 이벤트 발생 시 호출할 콜백 함수
            priority: 리스너 우선순위 (높을수록 먼저 실행)
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
            
        subscriber = EventSubscriber(callback, priority)
        self._listeners[event_type].append(subscriber)
        self._listeners[event_type].sort(key=lambda x: x.priority, reverse=True)
        
        logger.debug(f"Added listener for event '{event_type}' with priority {priority}")
        
    def once(self, event_type: str, callback: Callable, priority: int = 0) -> None:
        """한 번만 실행되는 이벤트 리스너 등록"""
        def one_time_callback(data: Any):
            self.remove_listener(event_type, one_time_callback)
            callback(data)
            
        self.on(event_type, one_time_callback, priority)
        logger.debug(f"Added one-time listener for event '{event_type}'")
        
    def emit(self, event: Event) -> None:
        """
        이벤트 발생 및 처리
        
        Args:
            event: 발생시킬 이벤트 객체
        """
        if event.type in self._listeners:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
                
            for subscriber in self._listeners[event.type]:
                try:
                    subscriber.callback(event.data)
                except Exception as e:
                    logger.error(f"Error in event handler for '{event.type}': {str(e)}")
                    
            logger.debug(f"Emitted event '{event.type}' with {len(self._listeners[event.type])} listeners")
        
    def remove_listener(self, event_type: str, callback: Callable) -> None:
        """
        특정 이벤트의 리스너 제거
        
        Args:
            event_type: 이벤트 타입
            callback: 제거할 콜백 함수
        """
        if event_type in self._listeners:
            self._listeners[event_type] = [
                subscriber for subscriber in self._listeners[event_type]
                if subscriber.callback != callback
            ]
            logger.debug(f"Removed listener for event '{event_type}'")
            
    def remove_all_listeners(self, event_type: Optional[str] = None) -> None:
        """
        모든 리스너 제거
        
        Args:
            event_type: 특정 이벤트 타입의 리스너만 제거할 경우 지정
        """
        if event_type:
            self._listeners[event_type] = []
            logger.debug(f"Removed all listeners for event '{event_type}'")
        else:
            self._listeners.clear()
            logger.debug("Removed all event listeners")
            
    def listener_count(self, event_type: str) -> int:
        """특정 이벤트의 리스너 수 반환"""
        return len(self._listeners.get(event_type, []))
        
    def get_event_history(self, event_type: Optional[str] = None) -> List[Event]:
        """
        이벤트 히스토리 조회
        
        Args:
            event_type: 특정 이벤트 타입의 히스토리만 조회할 경우 지정
        """
        if event_type:
            return [event for event in self._event_history if event.type == event_type]
        return self._event_history.copy()