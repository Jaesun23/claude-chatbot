import os
import json
from typing import Dict, Optional
from chat_session import ChatSession
from encryption import encrypt_data, decrypt_data
import logging

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self, storage_dir: str = "conversations"):
        """
        대화 관리자를 초기화합니다.
        
        Args:
            storage_dir: 대화 저장 디렉토리 경로
        """
        self.storage_dir = storage_dir
        self.sessions: Dict[str, ChatSession] = {}
        self.current_session: Optional[str] = None

        # 스토리지 디렉토리 생성
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)

        # 기본 세션 생성
        self.create_new_session("Default Session")
        
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
        
        new_session = ChatSession()
        self.sessions[session_name] = new_session
        
        # 첫 세션이거나 현재 세션이 없는 경우 현재 세션으로 설정
        if self.current_session is None:
            self.current_session = session_name
            
        return new_session

    def get_current_session(self) -> ChatSession:
        """
        현재 활성화된 세션을 반환합니다.
        없는 경우 새로 생성합니다.
        
        Returns:
            ChatSession: 현재 활성화된 세션
        """
        if self.current_session is None or self.current_session not in self.sessions:
            self.create_new_session("Default Session")
        return self.sessions[self.current_session]

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
        return self.sessions[session_name]

    def list_sessions(self) -> list:
        """
        세션 목록을 반환합니다.
        
        Returns:
            list: 세션 이름 목록
        """
        return list(self.sessions.keys())

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
        if self.current_session == old_name:
            self.current_session = new_name
            
        # 파일 이름도 변경
        old_path = os.path.join(self.storage_dir, f"{old_name}.enc")
        new_path = os.path.join(self.storage_dir, f"{new_name}.enc")
        if os.path.exists(old_path):
            os.rename(old_path, new_path)

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
                "messages": session.messages,
                "context": session.context_manager.active_context
            }
            
            # 데이터 암호화 및 저장
            encrypted_data = encrypt_data(json.dumps(session_data))
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
                
            logger.info(f"Session '{session_name}' saved successfully")
                
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
            
            new_session = ChatSession()
            if 'messages' in session_data:
                for message in session_data['messages']:
                    new_session.add_message(message['role'], message['content'])
                    
            if 'context' in session_data:
                new_session.context_manager.set_context(session_data['context'])
                
            self.sessions[session_name] = new_session
            logger.info(f"Session '{session_name}' loaded successfully")
            return new_session
            
        except Exception as e:
            logger.error(f"Failed to load session '{session_name}': {str(e)}")
            raise

    def delete_session(self, session_name: str = None) -> None:
        """
        세션을 삭제합니다.
        
        Args:
            session_name: 삭제할 세션의 이름. None인 경우 현재 세션 삭제
        """
        if session_name is None:
            session_name = self.current_session
            
        if session_name not in self.sessions:
            raise ValueError(f"Session '{session_name}' not found")
            
        # 파일 삭제
        file_path = os.path.join(self.storage_dir, f"{session_name}.enc")
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # 세션 객체 삭제
        del self.sessions[session_name]
        
        # 현재 세션이 삭제된 경우 다른 세션으로 전환
        if self.current_session == session_name:
            if self.sessions:
                self.current_session = next(iter(self.sessions))
            else:
                # 모든 세션이 삭제된 경우 새 기본 세션 생성
                self.create_new_session("Default Session")

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