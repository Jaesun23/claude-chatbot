import os
import json
from tkinter import messagebox

class ConfigManager:
    """설정을 관리하는 클래스입니다."""
    
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chat_config.json')
    DEFAULT_CONFIG = {
        'window_size': '800x600',
        'theme': 'dark',
        'font_size': 10,
        'user_name': 'User'
    }

    @classmethod
    def load_config(cls):
        """
        설정 파일을 로드합니다.
        파일이 없거나 오류가 있는 경우 기본 설정을 반환합니다.
        
        Returns:
            dict: 설정 딕셔너리
        """
        try:
            if os.path.exists(cls.CONFIG_FILE):
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except json.JSONDecodeError:
            messagebox.showerror("Error", "설정 파일 형식이 올바르지 않습니다. 기본 설정을 사용합니다.")
        except IOError as e:
            messagebox.showerror("Error", f"설정 파일을 읽는 중 오류가 발생했습니다: {e}")
        return cls.DEFAULT_CONFIG.copy()

    @classmethod
    def save_config(cls, config):
        """
        설정을 파일에 저장합니다.
        
        Args:
            config (dict): 저장할 설정 딕셔너리
        """
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except IOError as e:
            messagebox.showerror("Error", f"설정 파일을 저장하는 중 오류가 발생했습니다: {e}")