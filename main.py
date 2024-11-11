import tkinter as tk
from tkinter import messagebox
from ui_manager import UIManager
from conversation_manager import ConversationManager  # SessionManager가 아닌 ConversationManager 사용
from config_manager import ConfigManager
from utils import decrypt_api_key
import logging
import sys
import os
from dotenv import load_dotenv
import asyncio
import tracemalloc

# tracemalloc 시작
tracemalloc.start()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('chat_app.log')
    ]
)
logger = logging.getLogger(__name__)

class ChatApp:
    def __init__(self, master):
        """
        채팅 애플리케이션을 초기화합니다.
        
        Args:
            master: 메인 tkinter 윈도우
        """
        self.master = master
        
        # 환경 변수 로드
        logger.info("Loading environment variables...")
        load_dotenv()
        
        # API 키 복호화 시도
        try:
            logger.info("Attempting to decrypt API key...")
            api_key = decrypt_api_key()
            os.environ['ANTHROPIC_API_KEY'] = api_key
            logger.info("API key successfully decrypted and set")
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {str(e)}")
            self.show_error(f"API 키 복호화 중 오류 발생: {str(e)}")
            self.master.destroy()
            return
            
        try:
            # 설정 로드
            logger.info("Loading configuration...")
            self.config = ConfigManager.load_config()
            
            # 대화 관리자 초기화
            logger.info("Initializing conversation manager...")
            self.conversation_manager = ConversationManager()
            
            # UI 매니저 초기화
            logger.info("Initializing UI manager...")
            self.ui_manager = UIManager(master, self.config, self.conversation_manager)
            self.ui_manager.chat_app = self
            
            # 윈도우 설정
            logger.info("Setting up window...")
            self.setup_window()
            
            logger.info("Application initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
            self.show_error(f"애플리케이션 초기화 중 오류 발생: {str(e)}")
            self.master.destroy()
            return

    def setup_window(self):
        """윈도우 설정을 초기화합니다."""
        # 기본 윈도우 크기 설정
        if 'window_size' in self.config:
            self.master.geometry(self.config['window_size'])
            
        # 종료 프로토콜 설정
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 윈도우 제목 설정
        self.master.title("Claude Chat Application")

    def show_error(self, message: str):
        """
        에러 메시지를 표시합니다.
        
        Args:
            message (str): 표시할 에러 메시지
        """
        logger.error(message)
        messagebox.showerror("Error", message)

    def on_closing(self):
        """애플리케이션 종료 시 처리할 작업을 수행합니다."""
        try:
            logger.info("Starting application shutdown...")
            # 현재 윈도우 크기 저장
            self.config['window_size'] = f"{self.master.winfo_width()}x{self.master.winfo_height()}"
            ConfigManager.save_config(self.config)
            
            # 대화 매니저 정리
            if hasattr(self, 'conversation_manager'):
                logger.info("Saving all conversations...")
                self.conversation_manager.save_all_sessions()
                
            logger.info("Application shutdown complete")
                
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}", exc_info=True)
        
        finally:
            self.master.destroy()

    async def send_message_async(self, event=None):
        """
        메시지 전송을 비동기적으로 처리합니다.
        
        Args:
            event: 이벤트 객체 (키보드 이벤트 등)
        """
        await self.ui_manager.send_message(event)

    def send_message(self, event=None):
        """
        메시지 전송을 처리합니다.
        
        Args:
            event: 이벤트 객체 (키보드 이벤트 등)
        """
        asyncio.run(self.send_message_async(event))
        return "break"

if __name__ == "__main__":
    try:
        logger.info("Starting application...")
        root = tk.Tk()
        app = ChatApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)