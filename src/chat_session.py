import anthropic
from anthropic import Anthropic
from typing import List, Dict, Optional, Any, Union
import json
import asyncio
from dataclasses import dataclass
import logging
from encryption import encrypt_data, decrypt_data
from response_formatter import format_response
from utils import count_tokens, decrypt_api_key
from vision_handler import VisionHandler
from context_manager import ContextManager
from retry_handler import RetryHandler

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MessageContent:
    """메시지 내용을 표현하는 데이터 클래스"""
    role: str
    content: Union[str, List[Dict]]
    metadata: Optional[Dict] = None

class ChatSession:
    """Claude API와의 대화 세션을 관리하는 클래스"""
    
    def __init__(self, 
                 model: str = "claude-3-5-sonnet-20241022", 
                 max_tokens: int = 8000, 
                 temperature: float = 0.1,
                 name: str = "Default Session"):
        """
        ChatSession 인스턴스를 초기화합니다.

        Args:
            model (str): 사용할 Claude 모델 이름
            max_tokens (int): 최대 토큰 수
            temperature (float): 응답의 무작위성 정도 (0.0 ~ 1.0)
            name (str): 세션 이름
        """
        try:
            api_key = decrypt_api_key()
            self.client = Anthropic(api_key=api_key)
        except Exception as e:
            logger.error(f"API 클라이언트 초기화 실패: {str(e)}")
            raise

        # 기본 설정
        self.name = name
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # 대화 관련 속성
        self.messages: List[MessageContent] = []
        self.total_tokens_used = 0
        
        # 컴포넌트 초기화
        self.vision_handler = VisionHandler()
        self.context_manager = ContextManager()
        self.retry_handler = RetryHandler(max_retries=3, base_delay=1.0)
        
        # 기본 에러 핸들러 등록
        self._register_default_error_handlers()
        
        logger.info(f"ChatSession '{name}' initialized with model {model}")

    def _register_default_error_handlers(self):
        """기본 에러 핸들러를 등록합니다."""
        def handle_api_error(error: anthropic.APIError, attempt: int):
            logger.warning(f"API 오류 발생 (시도 {attempt + 1}/{self.retry_handler.max_retries}): {str(error)}")
            if error.status_code == 401:
                logger.error("인증 오류: API 키를 확인하세요.")
            elif error.status_code == 429:
                logger.warning("요청 한도 초과: 잠시 후 다시 시도합니다.")
            elif error.status_code == 500:
                logger.error("서버 오류: Anthropic 서버에 문제가 발생했습니다.")

        def handle_general_error(error: Exception, attempt: int):
            logger.warning(f"일반 오류 발생 (시도 {attempt + 1}/{self.retry_handler.max_retries}): {str(error)}")

        self.retry_handler.register_error_handler(anthropic.APIError, handle_api_error)
        self.retry_handler.register_error_handler(Exception, handle_general_error)

    def add_message(self, role: str, content: Union[str, List[Dict]], metadata: Optional[Dict] = None):
        """
        대화 기록에 새 메시지를 추가합니다.

        Args:
            role (str): 메시지 작성자의 역할 ('user' 또는 'assistant')
            content (Union[str, List[Dict]]): 메시지 내용
            metadata (Optional[Dict]): 메시지 관련 메타데이터
        """
        message = MessageContent(role=role, content=content, metadata=metadata)
        self.messages.append(message)
        logger.debug(f"Added message from {role} with content length {len(str(content))}")

    async def get_response(self, user_input: str) -> str:
        """
        사용자 입력에 대한 Claude의 응답을 비동기적으로 가져옵니다.

        Args:
            user_input (str): 사용자 입력 메시지

        Returns:
            str: Claude의 응답 메시지
        """
        self.add_message("user", user_input)
        
        try:
            async def make_request():
                messages = [{"role": msg.role, "content": msg.content} for msg in self.messages]
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=messages,
                    system=self.context_manager.get_current_system_prompt()
                )
                return response.content[0].text

            assistant_message = await self.retry_handler.async_retry(make_request)
            self.add_message("assistant", assistant_message)
            
            # 토큰 사용량 업데이트 (근사값 사용)
            self.total_tokens_used += count_tokens([{"role": "user", "content": user_input}])
            self.total_tokens_used += count_tokens([{"role": "assistant", "content": assistant_message}])
            
            return format_response(assistant_message)
            
        except Exception as e:
            error_message = f"응답 생성 중 오류 발생: {str(e)}"
            logger.error(error_message)
            return error_message

    async def process_image_message(self, message: str, image_path: str) -> str:
        """
        이미지와 텍스트를 함께 처리하여 응답을 생성합니다.

        Args:
            message (str): 이미지와 함께 전송할 텍스트 메시지
            image_path (str): 이미지 파일 경로

        Returns:
            str: Claude의 응답 메시지
        """
        try:
            image_content = self.vision_handler.prepare_image_content(image_path)
            
            content = [
                {'type': 'text', 'text': message},
                image_content
            ]
            
            self.add_message("user", content, {"image_path": image_path})
            
            async def make_request():
                messages = [{"role": msg.role, "content": msg.content} for msg in self.messages]
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=messages,
                    system=self.context_manager.get_current_system_prompt()
                )
                return response.content[0].text

            assistant_message = await self.retry_handler.async_retry(make_request)
            self.add_message("assistant", assistant_message)
            
            return format_response(assistant_message)
            
        except Exception as e:
            error_message = f"이미지 처리 중 오류 발생: {str(e)}"
            logger.error(error_message)
            return error_message

    def save_session(self, filename: str):
        """
        현재 세션 상태를 파일로 저장합니다.

        Args:
            filename (str): 저장할 파일 경로
        """
        try:
            data = {
                "name": self.name,
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [{"role": msg.role, "content": msg.content, "metadata": msg.metadata} 
                           for msg in self.messages],
                "total_tokens_used": self.total_tokens_used,
                "active_context": self.context_manager.active_context,
                "context_history": self.context_manager.get_context_history(),
                "custom_contexts": {k: v for k, v in self.context_manager.system_prompts.items() 
                                 if k not in ContextManager.DEFAULT_CONTEXTS}
            }
            
            encrypted_data = encrypt_data(json.dumps(data))
            with open(filename, 'wb') as f:
                f.write(encrypted_data)
                
            logger.info(f"Session saved to {filename}")
                
        except Exception as e:
            error_message = f"세션 저장 중 오류 발생: {str(e)}"
            logger.error(error_message)
            raise

    @classmethod
    def load_session(cls, filename: str) -> 'ChatSession':
        """
        저장된 세션을 로드하여 새 ChatSession 인스턴스를 생성합니다.

        Args:
            filename (str): 로드할 파일 경로

        Returns:
            ChatSession: 로드된 세션 인스턴스
        """
        try:
            with open(filename, 'rb') as f:
                encrypted_data = f.read()
                
            decrypted_data = decrypt_data(encrypted_data)
            data = json.loads(decrypted_data)
            
            # 새 인스턴스 생성
            session = cls(
                model=data["model"],
                max_tokens=data["max_tokens"],
                temperature=data["temperature"],
                name=data["name"]
            )
            
            # 상태 복원
            for msg_data in data["messages"]:
                session.add_message(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    metadata=msg_data.get("metadata")
                )
            
            session.total_tokens_used = data["total_tokens_used"]
            
            # 컨텍스트 복원
            if "custom_contexts" in data:
                for name, prompt in data["custom_contexts"].items():
                    session.context_manager.add_custom_context(name, prompt)
            
            if "active_context" in data:
                session.context_manager.set_context(data["active_context"])
            
            logger.info(f"Session loaded from {filename}")
            return session
            
        except Exception as e:
            error_message = f"세션 로드 중 오류 발생: {str(e)}"
            logger.error(error_message)
            raise

    def get_token_usage(self) -> Dict[str, int]:
        """
        토큰 사용량 통계를 반환합니다.

        Returns:
            Dict[str, int]: 토큰 사용량 정보
        """
        return {
            "total_tokens": self.total_tokens_used,
            "available_tokens": self.max_tokens - self.total_tokens_used
        }

    def clear_context(self):
        """현재 컨텍스트를 초기화합니다."""
        self.context_manager.set_context("general")
        logger.info("Context reset to general")

    def __str__(self) -> str:
        """세션의 문자열 표현을 반환합니다."""
        return f"ChatSession(name='{self.name}', model='{self.model}', messages={len(self.messages)})"

    def __repr__(self) -> str:
        """세션의 개발자용 문자열 표현을 반환합니다."""
        return f"ChatSession(name='{self.name}', model='{self.model}', max_tokens={self.max_tokens}, temperature={self.temperature})"