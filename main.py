import tkinter as tk
import asyncio
import logging
from service_container import ServiceContainer
import traceback
import sys
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/chat_app.log')
    ]
)

logger = logging.getLogger(__name__)

class ChatApplication:
    """채팅 애플리케이션 메인 클래스"""
    
    def __init__(self):
        self.container = ServiceContainer.get_instance()
        self.root = None
        
    async def initialize(self):
        """애플리케이션 초기화"""
        try:
            # 서비스 컨테이너 초기화
            await self.container.initialize()
            
            # UI 가져오기
            chat_ui = self.container.get_service('chat_ui')
            self.root = chat_ui.root
            
            logger.info("Chat application initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}")
            raise
            
    def run(self):
        """애플리케이션 실행"""
        if self.root is None:
            raise RuntimeError("Application not initialized")
            
        try:
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            raise
        finally:
            asyncio.run(self.container.cleanup())
            
    async def cleanup(self):
        """애플리케이션 정리"""
        try:
            await self.container.cleanup()
            logger.info("Application cleanup complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

async def main():
    """메인 함수"""
    # 필요한 디렉토리 생성
    Path("logs").mkdir(exist_ok=True)
    
    try:
        app = ChatApplication()
        await app.initialize()
        app.run()
    except Exception as e:
        logger.error(f"Application error: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 