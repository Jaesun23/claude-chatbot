from enum import Enum, auto

class UIEventType(Enum):
    """UI 관련 이벤트 타입 정의"""
    
    # 메시지 관련 이벤트
    SEND_MESSAGE = auto()
    RECEIVE_MESSAGE = auto()
    MESSAGE_SENDING = auto()
    MESSAGE_SENT = auto()
    
    # 세션 관련 이벤트
    SESSION_SWITCH = auto()
    SESSION_CREATED = auto()
    SESSION_DELETED = auto()
    
    # UI 상태 이벤트
    THEME_CHANGE = auto()
    FONT_CHANGE = auto()
    WINDOW_RESIZE = auto()
    
    # 파일 관련 이벤트
    FILE_ATTACH = auto()
    FILE_PROCESS = auto()
    
    # 에러 관련 이벤트
    ERROR_OCCURRED = auto()
    WARNING_OCCURRED = auto()
    
    # 상태 변경 이벤트
    STATE_CHANGE = auto()
    LOADING_START = auto()
    LOADING_END = auto()

class UIEventData:
    """UI 이벤트 데이터 구조체"""
    
    @staticmethod
    def message(content: str, **kwargs):
        return {
            "content": content,
            **kwargs
        }
    
    @staticmethod
    def session(session_id: str, **kwargs):
        return {
            "session_id": session_id,
            **kwargs
        }
    
    @staticmethod
    def theme(theme_name: str, **kwargs):
        return {
            "theme": theme_name,
            **kwargs
        }
    
    @staticmethod
    def error(error_message: str, error_type: str = None, **kwargs):
        return {
            "message": error_message,
            "type": error_type,
            **kwargs
        }
    
    @staticmethod
    def state(state_name: str, data: dict = None, **kwargs):
        return {
            "state": state_name,
            "data": data or {},
            **kwargs
        }