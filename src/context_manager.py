from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ContextManager:
    """대화 컨텍스트와 시스템 프롬프트를 관리하는 클래스"""
    
    DEFAULT_CONTEXTS = {
        "general": "You are Claude, a helpful AI assistant.",
        "code_review": """You are a skilled Python developer tasked with reviewing and improving code.
                         Focus on identifying bugs, suggesting optimizations, and ensuring best practices.
                         Use clear explanations and provide specific code examples.""",
        "teacher": """You are an expert teacher, skilled at explaining complex concepts in simple terms.
                     Break down difficult topics into understandable parts and use relevant examples.
                     Encourage questions and provide step-by-step explanations.""",
        "translator": """You are a professional translator with expertise in multiple languages.
                        Provide accurate translations while maintaining context and nuance.
                        Explain cultural context when relevant.""",
        "writer": """You are a creative writer, skilled in various writing styles and formats.
                    Help with writing, editing, and improving text content.
                    Provide constructive feedback and suggestions."""
    }

    def __init__(self):
        """
        ContextManager 인스턴스를 초기화합니다.
        기본 컨텍스트들을 복사하고 초기 상태를 설정합니다.
        """
        self.system_prompts: Dict[str, str] = self.DEFAULT_CONTEXTS.copy()
        self.active_context: str = "general"
        self.context_history: List[dict] = []
        self.max_history: int = 10
        self.last_change: datetime = datetime.now()

        logger.info("Context manager initialized with default contexts")

    def set_context(self, context_type: str) -> str:
        """
        컨텍스트를 변경하고 해당하는 시스템 프롬프트를 반환합니다.

        Args:
            context_type (str): 변경할 컨텍스트 타입

        Returns:
            str: 설정된 시스템 프롬프트

        Raises:
            ValueError: 존재하지 않는 컨텍스트 타입인 경우
        """
        if context_type not in self.system_prompts:
            error_msg = f"Unknown context type: {context_type}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.active_context = context_type
        self.last_change = datetime.now()
        
        # 컨텍스트 변경 기록 추가
        self.context_history.append({
            'context': context_type,
            'timestamp': self.last_change
        })
        
        # 최대 히스토리 개수 유지
        if len(self.context_history) > self.max_history:
            self.context_history.pop(0)
            
        logger.info(f"Context changed to: {context_type}")
        return self.get_current_system_prompt()

    def get_current_system_prompt(self) -> str:
        """
        현재 활성화된 컨텍스트의 시스템 프롬프트를 반환합니다.

        Returns:
            str: 현재 시스템 프롬프트
        """
        return self.system_prompts[self.active_context]

    def add_custom_context(self, name: str, prompt: str) -> None:
        """
        새로운 커스텀 컨텍스트를 추가합니다.

        Args:
            name (str): 새 컨텍스트의 이름
            prompt (str): 새 컨텍스트의 시스템 프롬프트

        Raises:
            ValueError: 기본 컨텍스트를 덮어쓰려고 할 경우
        """
        if name in self.DEFAULT_CONTEXTS:
            error_msg = f"Cannot override default context: {name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        self.system_prompts[name] = prompt
        logger.info(f"Added new custom context: {name}")

    def remove_custom_context(self, name: str) -> None:
        """
        커스텀 컨텍스트를 제거합니다.

        Args:
            name (str): 제거할 컨텍스트의 이름

        Raises:
            ValueError: 기본 컨텍스트를 제거하려고 하거나 존재하지 않는 컨텍스트인 경우
        """
        if name in self.DEFAULT_CONTEXTS:
            error_msg = f"Cannot remove default context: {name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        if name not in self.system_prompts:
            error_msg = f"Context not found: {name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        del self.system_prompts[name]
        
        # 제거된 컨텍스트가 현재 활성 컨텍스트인 경우 general로 변경
        if self.active_context == name:
            self.set_context("general")
            
        logger.info(f"Removed custom context: {name}")

    def get_context_history(self) -> List[dict]:
        """
        컨텍스트 변경 히스토리를 반환합니다.

        Returns:
            List[dict]: 컨텍스트 변경 히스토리
        """
        return self.context_history.copy()

    def get_available_contexts(self) -> List[str]:
        """
        사용 가능한 모든 컨텍스트 목록을 반환합니다.

        Returns:
            List[str]: 사용 가능한 컨텍스트 이름 목록
        """
        return list(self.system_prompts.keys())

    def get_context_details(self, context_name: str) -> Optional[dict]:
        """
        특정 컨텍스트의 상세 정보를 반환합니다.

        Args:
            context_name (str): 조회할 컨텍스트 이름

        Returns:
            Optional[dict]: 컨텍스트 정보 또는 None
        """
        if context_name not in self.system_prompts:
            return None
            
        return {
            'name': context_name,
            'prompt': self.system_prompts[context_name],
            'is_default': context_name in self.DEFAULT_CONTEXTS,
            'is_active': context_name == self.active_context
        }

    def reset_to_default(self) -> None:
        """
        모든 커스텀 컨텍스트를 제거하고 기본 상태로 초기화합니다.
        """
        self.system_prompts = self.DEFAULT_CONTEXTS.copy()
        self.active_context = "general"
        self.context_history = []
        self.last_change = datetime.now()
        logger.info("Context manager reset to default state")