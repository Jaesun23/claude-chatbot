from typing import Optional, Dict, Any
from events import EventEmitter
from ui.chat_ui import ChatUI
from controllers.chat_controller import ChatController
from conversation_manager import ConversationManager
from config_manager import ConfigManager
import logging
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class ServiceContainer:
    """애플리케이션의 서비스 컨테이너
    
    모든 주요 컴포넌트의 생성과 의존성을 관리합니다.
    싱글톤 패턴을 사용하여 전역적인 접근을 제공합니다.
    """
    
    _instance: Optional['ServiceContainer'] = None
    
    @classmethod
    def get_instance(cls) -> 'ServiceContainer':
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if ServiceContainer._instance is not None:
            raise RuntimeError("ServiceContainer is a singleton. Use get_instance() instead.")
            
        self._services: Dict[str, Any] = {}
        self._initialized = False
        
        # 기본 이벤트 이미터 생성
        self._event_emitter = EventEmitter()
        logger.info("ServiceContainer created")
        
    async def initialize(self, config_path: str = "config/config.json"):
        """서비스 컨테이너 초기화"""
        if self._initialized:
            logger.warning("ServiceContainer already initialized")
            return
            
        try:
            # 설정 관리자 초기화
            self._services['config_manager'] = ConfigManager(config_path)
            config = self._services['config_manager'].load_config()
            
            # 기본 디렉토리 생성
            self._create_directories(config)
            
            # 컴포넌트 초기화
            await self._initialize_components(config)
            
            self._initialized = True
            logger.info("ServiceContainer initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize ServiceContainer: {str(e)}")
            raise
            
    def _create_directories(self, config: Dict[str, Any]):
        """필요한 디렉토리 생성"""
        directories = [
            config.get('storage_dir', 'storage'),
            config.get('cache_dir', 'cache'),
            config.get('log_dir', 'logs'),
            'config'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
    async def _initialize_components(self, config: Dict[str, Any]):
        """각 컴포넌트 초기화"""
        try:
            # ConversationManager 초기화
            self._services['conversation_manager'] = ConversationManager(
                storage_dir=config.get('storage_dir', 'storage')
            )
            
            # ChatController 초기화
            self._services['chat_controller'] = ChatController(
                self._event_emitter,
                self._services['conversation_manager']
            )
            await self._services['chat_controller'].initialize()
            
            # ChatUI 초기화
            self._services['chat_ui'] = ChatUI(
                self._event_emitter,
                config
            )
            
        except Exception as e:
            logger.error(f"Component initialization failed: {str(e)}")
            raise
            
    def get_service(self, service_name: str) -> Any:
        """서비스 인스턴스 반환"""
        if not self._initialized:
            raise RuntimeError("ServiceContainer not initialized")
            
        service = self._services.get(service_name)
        if service is None:
            raise KeyError(f"Service not found: {service_name}")
            
        return service
        
    def get_event_emitter(self) -> EventEmitter:
        """이벤트 이미터 반환"""
        return self._event_emitter
        
    async def cleanup(self):
        """컨테이너 정리"""
        if not self._initialized:
            return
            
        try:
            # 컨트롤러 정리
            if 'chat_controller' in self._services:
                await self._services['chat_controller'].cleanup()
                
            # 대화 관리자 정리
            if 'conversation_manager' in self._services:
                self._services['conversation_manager'].save_all_sessions()
                
            # 설정 저장
            if 'config_manager' in self._services:
                self._services['config_manager'].save_config()
                
            self._services.clear()
            self._initialized = False
            
            logger.info("ServiceContainer cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during ServiceContainer cleanup: {str(e)}")
            raise
            
    def __del__(self):
        """소멸자"""
        if self._initialized:
            asyncio.run(self.cleanup())

class ServiceContainerAware:
    """서비스 컨테이너 접근이 필요한 클래스들의 기본 클래스"""
    
    def __init__(self):
        self._container = ServiceContainer.get_instance()
        
    @property
    def container(self) -> ServiceContainer:
        return self._container
        
    @property
    def event_emitter(self) -> EventEmitter:
        return self._container.get_event_emitter()