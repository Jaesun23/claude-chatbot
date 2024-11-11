from typing import Dict, Any
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class ThemeColors:
    """테마 색상 정의"""
    background: str
    foreground: str
    input_bg: str
    input_fg: str
    button_bg: str
    button_fg: str
    highlight_bg: str
    highlight_fg: str
    error: str
    success: str
    warning: str

class ThemeManager:
    """테마 관리 클래스"""
    
    # 기본 테마 정의
    DEFAULT_THEMES = {
        "light": ThemeColors(
            background="#ffffff",
            foreground="#000000",
            input_bg="#f5f5f5",
            input_fg="#000000",
            button_bg="#e0e0e0",
            button_fg="#000000",
            highlight_bg="#e3f2fd",
            highlight_fg="#1565c0",
            error="#f44336",
            success="#4caf50",
            warning="#ff9800"
        ),
        "dark": ThemeColors(
            background="#2b2b2b",
            foreground="#ffffff",
            input_bg="#383838",
            input_fg="#ffffff",
            button_bg="#404040",
            button_fg="#ffffff",
            highlight_bg="#1e3d5c",
            highlight_fg="#90caf9",
            error="#ef5350",
            success="#66bb6a",
            warning="#ffb74d"
        )
    }

    def __init__(self):
        self.custom_themes: Dict[str, ThemeColors] = {}
        self.current_theme = "light"
        self._load_custom_themes()
        logger.info("ThemeManager initialized")
        
    def _load_custom_themes(self):
        """사용자 정의 테마 로드"""
        try:
            with open('config/custom_themes.json', 'r') as f:
                themes = json.load(f)
                for name, colors in themes.items():
                    self.custom_themes[name] = ThemeColors(**colors)
            logger.info(f"Loaded {len(self.custom_themes)} custom themes")
        except FileNotFoundError:
            logger.debug("No custom themes file found")
        except Exception as e:
            logger.error(f"Error loading custom themes: {str(e)}")

    def get_theme(self, name: str) -> ThemeColors:
        """테마 색상 가져오기"""
        if name in self.DEFAULT_THEMES:
            return self.DEFAULT_THEMES[name]
        elif name in self.custom_themes:
            return self.custom_themes[name]
        else:
            logger.warning(f"Theme '{name}' not found, using default light theme")
            return self.DEFAULT_THEMES["light"]
            
    def apply_theme(self, root: tk.Tk, name: str):
        """테마를 UI에 적용"""
        theme = self.get_theme(name)
        self.current_theme = name
        
        style = ttk.Style()
        
        # TTK 스타일 설정
        style.configure("TFrame", background=theme.background)
        style.configure("TLabel", 
            background=theme.background,
            foreground=theme.foreground
        )
        style.configure("TButton",
            background=theme.button_bg,
            foreground=theme.button_fg,
            bordercolor=theme.button_bg
        )
        style.configure("TEntry",
            fieldbackground=theme.input_bg,
            foreground=theme.input_fg
        )
        
        # 기본 위젯 설정
        root.configure(bg=theme.background)
        
        # 모든 자식 위젯에 테마 적용
        self._apply_theme_to_widget(root, theme)
        
        logger.info(f"Applied theme: {name}")
        
    def _apply_theme_to_widget(self, widget: tk.Widget, theme: ThemeColors):
        """재귀적으로 모든 위젯에 테마 적용"""
        try:
            # Text 위젯 특별 처리
            if isinstance(widget, tk.Text):
                widget.configure(
                    bg=theme.input_bg,
                    fg=theme.input_fg,
                    insertbackground=theme.foreground,
                    selectbackground=theme.highlight_bg,
                    selectforeground=theme.highlight_fg
                )
                
                # 태그 색상 설정
                widget.tag_configure("error", foreground=theme.error)
                widget.tag_configure("success", foreground=theme.success)
                widget.tag_configure("warning", foreground=theme.warning)
                
            # ScrolledText 특별 처리
            elif isinstance(widget, tk.scrolledtext.ScrolledText):
                widget.configure(
                    bg=theme.input_bg,
                    fg=theme.input_fg,
                    insertbackground=theme.foreground,
                    selectbackground=theme.highlight_bg,
                    selectforeground=theme.highlight_fg
                )
                
            # 일반 위젯 처리
            elif not isinstance(widget, ttk.Widget):  # TTK 위젯은 스타일로 처리
                if "bg" in widget.configure():
                    widget.configure(bg=theme.background)
                if "fg" in widget.configure():
                    widget.configure(fg=theme.foreground)
                    
            # 자식 위젯들에 대해 재귀적으로 적용
            for child in widget.winfo_children():
                self._apply_theme_to_widget(child, theme)
                
        except tk.TclError as e:
            logger.debug(f"Could not apply theme to widget: {str(e)}")
            
    def create_custom_theme(self, name: str, colors: Dict[str, str]):
        """사용자 정의 테마 생성"""
        try:
            theme_colors = ThemeColors(**colors)
            self.custom_themes[name] = theme_colors
            self._save_custom_themes()
            logger.info(f"Created custom theme: {name}")
            return True
        except Exception as e:
            logger.error(f"Error creating custom theme: {str(e)}")
            return False
            
    def _save_custom_themes(self):
        """사용자 정의 테마 저장"""
        try:
            theme_data = {
                name: vars(colors)
                for name, colors in self.custom_themes.items()
            }
            with open('config/custom_themes.json', 'w') as f:
                json.dump(theme_data, f, indent=2)
            logger.info("Saved custom themes")
        except Exception as e:
            logger.error(f"Error saving custom themes: {str(e)}")