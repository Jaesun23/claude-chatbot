import os
import json
from typing import Dict, Optional, List
from chat_session import ChatSession
from encryption import encrypt_data, decrypt_data
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConversationManager:
    """대화 세션들을 관리하는 클래스"""
    
    def __init__(self, storage_dir: str = "conversations"):
        """
        대화 관리자를 초기화합니다.
        
        Args:
            storage_dir: 대화 저장 디렉토리 경로
        """
        self.storage_dir = storage_dir
        self.sessions: Dict[str, ChatSession] = {}
        self.current_session: Optional[str] = None
        self.last_active: Dict[str, datetime] = {}

        # 스토리지 디렉토리 생성
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            logger.info(f"Created storage directory: {storage_dir}")

        # 저장된 세션들 로드
        self.load_all_sessions()
        
        # 기본 세션이 없으면 생성
        if not self.sessions:
            self.create_new_session("Default Session")
            logger.info("Created default session")

    def create_new_session(self, session_name: str) -> ChatSession:
        """
        새로운 세션을 생성합니다.
        
        Args:
            session_name: 새 세션의 이름
            
        Returns:
            ChatSession: 생성된 세션 객체
            
        Raises:
            ValueError: 동일한 이름의 세션이 이미 존재할 경우
        """
        if session_name in self.sessions:
            raise ValueError(f"Session '{session_name}' already exists")
        
        new_session = ChatSession(name=session_name)
        self.sessions[session_name] = new_session
        self.last_active[session_name] = datetime.now()
        
        # 첫 세션이거나 현재 세션이 없는 경우 현재 세션으로 설정
        if self.current_session is None:
            self.current_session = session_name
            
        logger.info(f"Created new session: {session_name}")
        return new_session

    def get_current_session(self) -> ChatSession:
        """
        현재 활성화된 세션을 반환합니다.
        세션이 없는 경우 새로 생성합니다.
        
        Returns:
            ChatSession: 현재 활성화된 세션
        """
        if self.current_session is None or self.current_session not in self.sessions:
            self.create_new_session("Default Session")
            logger.info("Created new default session as current session was invalid")
            
        session = self.sessions[self.current_session]
        self.last_active[self.current_session] = datetime.now()
        return session

    def switch_session(self, session_name: str) -> ChatSession:
        """
        지정된 세션으로 전환합니다.
        
        Args:
            session_name: 전환할 세션의 이름
            
        Returns:
            ChatSession: 전환된 세션 객체
            
        Raises:
            ValueError: 존재하지 않는 세션인 경우
        """
        if session_name not in self.sessions:
            raise ValueError(f"Session '{session_name}' not found")
        
        self.current_session = session_name
        self.last_active[session_name] = datetime.now()
        logger.info(f"Switched to session: {session_name}")
        return self.sessions[session_name]

    def list_sessions(self) -> List[str]:
        """
        세션 목록을 반환합니다.
        
        Returns:
            List[str]: 세션 이름 목록
        """
        return sorted(self.sessions.keys())

    def get_session_info(self, session_name: str) -> dict:
        """
        세션의 상세 정보를 반환합니다.
        
        Args:
            session_name: 정보를 조회할 세션 이름
            
        Returns:
            dict: 세션 정보 (이름, 메시지 수, 마지막 활성 시간 등)
            
        Raises:
            ValueError: 존재하지 않는 세션인 경우
        """
        if session_name not in self.sessions:
            raise ValueError(f"Session '{session_name}' not found")
            
        session = self.sessions[session_name]
        return {
            'name': session_name,
            'message_count': len(session.messages),
            'last_active': self.last_active[session_name],
            'is_current': session_name == self.current_session,
            'context': session.context_manager.active_context
        }

    def rename_session(self, old_name: str, new_name: str) -> None:
        """
        세션의 이름을 변경합니다.
        
        Args:
            old_name: 현재 세션 이름
            new_name: 새로운 세션 이름
            
        Raises:
            ValueError: 원래 세션이 없거나 새 이름의 세션이 이미 존재하는 경우
        """
        if old_name not in self.sessions:
            raise ValueError(f"Session '{old_name}' not found")
        if new_name in self.sessions:
            raise ValueError(f"Session '{new_name}' already exists")
            
        self.sessions[new_name] = self.sessions.pop(old_name)
        self.last_active[new_name] = self.last_active.pop(old_name)
        
        if self.current_session == old_name:
            self.current_session = new_name
            
        # 파일 이름도 변경
        old_path = os.path.join(self.storage_dir, f"{old_name}.enc")
        new_path = os.path.join(self.storage_dir, f"{new_name}.enc")
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            
        logger.info(f"Renamed session from '{old_name}' to '{new_name}'")

    def delete_session(self, session_name: Optional[str] = None) -> None:
        """
        세션을 삭제합니다.
        
        Args:
            session_name: 삭제할 세션의 이름. None인 경우 현재 세션 삭제
            
        Raises:
            ValueError: 삭제할 세션이 없는 경우
        """
        if session_name is None:
            session_name = self.current_session
            
        if session_name not in self.sessions:
            raise ValueError(f"Session '{session_name}' not found")
            
        # 마지막 세션은 삭제할 수 없음
        if len(self.sessions) == 1:
            raise ValueError("Cannot delete the last session")
            
        # 파일 삭제
        file_path = os.path.join(self.storage_dir, f"{session_name}.enc")
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # 세션 객체 삭제
        del self.sessions[session_name]
        del self.last_active[session_name]
        
        # 현재 세션이 삭제된 경우 다른 세션으로 전환
        if self.current_session == session_name:
            self.current_session = next(iter(self.sessions))
            
        logger.info(f"Deleted session: {session_name}")

    def save_session(self, session_name: str) -> None:
        """
        세션을 파일에 저장합니다.
        
        Args:
            session_name: 저장할 세션의 이름
            
        Raises:
            ValueError: 존재하지 않는 세션인 경우
        """
        if session_name not in self.sessions:
            raise ValueError(f"Session '{session_name}' not found")
            
        session = self.sessions[session_name]
        file_path = os.path.join(self.storage_dir, f"{session_name}.enc")
        
        try:
            # 세션 데이터 준비
            session_data = {
                "name": session_name,
                "messages": [msg.__dict__ for msg in session.messages],
                "context": session.context_manager.active_context,
                "last_active": self.last_active[session_name].isoformat()
            }
            
            # 데이터 암호화 및 저장
            encrypted_data = encrypt_data(json.dumps(session_data))
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
                
            logger.info(f"Saved session: {session_name}")
                
        except Exception as e:
            logger.error(f"Failed to save session '{session_name}': {str(e)}")
            raise

    def load_session(self, session_name: str) -> ChatSession:
        """
        저장된 세션을 로드합니다.
        
        Args:
            session_name: 로드할 세션의 이름
            
        Returns:
            ChatSession: 로드된 세션 객체
            
        Raises:
            FileNotFoundError: 세션 파일이 없는 경우
        """
        file_path = os.path.join(self.storage_dir, f"{session_name}.enc")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Session file for '{session_name}' not found")
        
        try:
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
                
            decrypted_data = decrypt_data(encrypted_data)
            session_data = json.loads(decrypted_data)
            
            new_session = ChatSession(name=session_name)
            
            # 메시지 복원
            for message_data in session_data['messages']:
                new_session.add_message(
                    role=message_data['role'],
                    content=message_data['content']
                )
                    
            # 컨텍스트 복원
            if 'context' in session_data:
                new_session.context_manager.set_context(session_data['context'])
                
            # 마지막 활성 시간 복원
            self.last_active[session_name] = datetime.fromisoformat(
                session_data.get('last_active', datetime.now().isoformat())
            )
                
            self.sessions[session_name] = new_session
            logger.info(f"Loaded session: {session_name}")
            return new_session
            
        except Exception as e:
            logger.error(f"Failed to load session '{session_name}': {str(e)}")
            raise

    def save_all_sessions(self) -> None:
        """모든 세션을 저장합니다."""
        for session_name in self.sessions:
            try:
                self.save_session(session_name)
            except Exception as e:
                logger.error(f"Failed to save session '{session_name}': {str(e)}")

    def load_all_sessions(self) -> None:
        """저장된 모든 세션을 로드합니다."""
        if os.path.exists(self.storage_dir):
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.enc'):
                    session_name = filename[:-4]  # .enc 제거
                    try:
                        self.load_session(session_name)
                    except Exception as e:
                        logger.error(f"Failed to load session '{session_name}': {str(e)}")

    def cleanup_old_sessions(self, days: int = 30) -> None:
        """
        오래된 세션들을 정리합니다.
        
        Args:
            days: 이 일수보다 오래된 세션들을 삭제
        """
        current_time = datetime.now()
        sessions_to_delete = []
        
        for session_name, last_active in self.last_active.items():
            if (current_time - last_active).days > days:
                sessions_to_delete.append(session_name)
                
        for session_name in sessions_to_delete:
            try:
                self.delete_session(session_name)
                logger.info(f"Cleaned up old session: {session_name}")
            except Exception as e:
                logger.error(f"Failed to cleanup session '{session_name}': {str(e)}")