from typing import Dict, Optional, Any
from events import EventEmitter, Event, UIEventType, UIEventData
from conversation_manager import ConversationManager
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ChatController:
    """채팅 애플리케이션의 비즈니스 로직을 처리하는 컨트롤러"""
    
    def __init__(self, event_emitter: EventEmitter, conversation_manager: ConversationManager):
        self.event_emitter = event_emitter
        self.conversation_manager = conversation_manager
        self.current_session = None
        self.is_processing = False
        
        # 이벤트 핸들러 등록
        self._setup_event_handlers()
        logger.info("ChatController initialized")
        
    def _setup_event_handlers(self):
        """이벤트 핸들러 설정"""
        # 메시지 관련 이벤트
        self.event_emitter.on(UIEventType.SEND_MESSAGE.value, self._handle_send_message)
        self.event_emitter.on(UIEventType.SESSION_SWITCH.value, self._handle_session_switch)
        
        # 파일 관련 이벤트
        self.event_emitter.on(UIEventType.FILE_ATTACH.value, self._handle_file_attach)
        
        # 세션 관리 이벤트
        self.event_emitter.on(UIEventType.SESSION_CREATED.value, self._handle_session_created)
        self.event_emitter.on(UIEventType.SESSION_DELETED.value, self._handle_session_deleted)
        
    async def _handle_send_message(self, data: Dict[str, Any]):
        """메시지 전송 처리"""
        if self.is_processing:
            logger.warning("Message processing in progress, ignoring new message")
            return
            
        self.is_processing = True
        
        try:
            # 상태 업데이트
            self.event_emitter.emit(Event(
                UIEventType.MESSAGE_SENDING.value,
                {"timestamp": datetime.now().isoformat()}
            ))
            
            # 현재 세션 가져오기
            session = self.conversation_manager.get_current_session()
            if not session:
                raise ValueError("No active session")
                
            # 메시지 전송
            response = await session.get_response(data["content"])
            
            # 응답 처리
            self.event_emitter.emit(Event(
                UIEventType.RECEIVE_MESSAGE.value,
                {
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session.id
                }
            ))
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            self.event_emitter.emit(Event(
                UIEventType.ERROR_OCCURRED.value,
                UIEventData.error(str(e), type(e).__name__)
            ))
            
        finally:
            self.is_processing = False
            self.event_emitter.emit(Event(
                UIEventType.MESSAGE_SENT.value,
                {"success": True}
            ))
            
    async def _handle_file_attach(self, data: Dict[str, Any]):
        """파일 첨부 처리"""
        try:
            session = self.conversation_manager.get_current_session()
            if not session:
                raise ValueError("No active session")
                
            # 파일 처리 상태 업데이트
            self.event_emitter.emit(Event(
                UIEventType.FILE_PROCESS.value,
                {"status": "processing", "filename": data["filename"]}
            ))
            
            # 이미지 처리 및 응답 생성
            response = await session.process_image_message(
                data.get("message", ""),
                data["file_path"]
            )
            
            # 응답 전송
            self.event_emitter.emit(Event(
                UIEventType.RECEIVE_MESSAGE.value,
                {
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session.id,
                    "has_image": True
                }
            ))
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            self.event_emitter.emit(Event(
                UIEventType.ERROR_OCCURRED.value,
                UIEventData.error(str(e), type(e).__name__)
            ))
            
    def _handle_session_switch(self, data: Dict[str, Any]):
        """세션 전환 처리"""
        try:
            session = self.conversation_manager.switch_session(data["session_id"])
            self.current_session = session
            
            # 세션 상태 업데이트
            self.event_emitter.emit(Event(
                UIEventType.STATE_CHANGE.value,
                UIEventData.state("session_changed", {
                    "session_id": session.id,
                    "message_count": len(session.messages)
                })
            ))
            
        except Exception as e:
            logger.error(f"Error switching session: {str(e)}")
            self.event_emitter.emit(Event(
                UIEventType.ERROR_OCCURRED.value,
                UIEventData.error(str(e), type(e).__name__)
            ))
            
    def _handle_session_created(self, data: Dict[str, Any]):
        """새 세션 생성 처리"""
        try:
            session = self.conversation_manager.create_new_session(data["name"])
            
            # 세션 목록 업데이트
            self.event_emitter.emit(Event(
                UIEventType.STATE_CHANGE.value,
                UIEventData.state("sessions_updated", {
                    "sessions": self.conversation_manager.list_sessions()
                })
            ))
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            self.event_emitter.emit(Event(
                UIEventType.ERROR_OCCURRED.value,
                UIEventData.error(str(e), type(e).__name__)
            ))
            
    def _handle_session_deleted(self, data: Dict[str, Any]):
        """세션 삭제 처리"""
        try:
            self.conversation_manager.delete_session(data["session_id"])
            
            # 세션 목록 업데이트
            self.event_emitter.emit(Event(
                UIEventType.STATE_CHANGE.value,
                UIEventData.state("sessions_updated", {
                    "sessions": self.conversation_manager.list_sessions()
                })
            ))
            
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            self.event_emitter.emit(Event(
                UIEventType.ERROR_OCCURRED.value,
                UIEventData.error(str(e), type(e).__name__)
            ))
            
    def initialize(self):
        """컨트롤러 초기화"""
        try:
            # 저장된 세션 로드
            self.conversation_manager.load_all_sessions()
            
            # 현재 세션 설정
            current_session = self.conversation_manager.get_current_session()
            if current_session:
                self.current_session = current_session
                
            # 초기 상태 이벤트 발생
            self.event_emitter.emit(Event(
                UIEventType.STATE_CHANGE.value,
                UIEventData.state("initialized", {
                    "sessions": self.conversation_manager.list_sessions(),
                    "current_session": current_session.id if current_session else None
                })
            ))
            
            logger.info("ChatController initialization complete")
            
        except Exception as e:
            logger.error(f"Error initializing controller: {str(e)}")
            self.event_emitter.emit(Event(
                UIEventType.ERROR_OCCURRED.value,
                UIEventData.error(str(e), type(e).__name__)
            ))
    
    def cleanup(self):
        """컨트롤러 정리"""
        try:
            # 모든 세션 저장
            self.conversation_manager.save_all_sessions()
            logger.info("ChatController cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            self.event_emitter.emit(Event(
                UIEventType.ERROR_OCCURRED.value,
                UIEventData.error(str(e), type(e).__name__)
            ))