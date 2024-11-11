import tkinter as tk
from tkinter import ttk, scrolledtext
import logging
from typing import Optional, Dict, Any
from events import EventEmitter, Event, UIEventType, UIEventData
from .theme import ThemeManager
from .context_menu import ContextMenuManager

logger = logging.getLogger(__name__)

class ChatUI:
    """이벤트 기반 채팅 UI 클래스"""
    
    def __init__(self, event_emitter: EventEmitter, config: Dict[str, Any]):
        self.event_emitter = event_emitter
        self.config = config
        self.root = tk.Tk()
        
        # 매니저 초기화
        self.theme_manager = ThemeManager()
        self.context_menu_manager = ContextMenuManager(event_emitter)
        
        # 윈도우 설정
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.title("Claude Chat")
        self.root.geometry(self.config.get('window_size', '800x600'))
        
        # UI 상태
        self.current_theme = self.config.get('theme', 'light')
        self.current_session = None
        self.is_sending = False
        
        # UI 초기화
        self._setup_ui()
        self._setup_event_handlers()
        self._setup_key_bindings()
        
        # 초기 테마 적용
        self.theme_manager.apply_theme(self.root, self.current_theme)
        
        logger.info("ChatUI initialized")
        
    def _setup_ui(self):
        """UI 컴포넌트 초기화"""
        # 메인 프레임 설정
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 컴포넌트 생성
        self._create_toolbar()
        self._create_chat_area()
        self._create_input_area()
        self._create_status_bar()
        
    def _create_toolbar(self):
        """상단 툴바 생성"""
        self.toolbar = ttk.Frame(self.main_frame)
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # 세션 관리 프레임
        self.session_frame = ttk.Frame(self.toolbar)
        self.session_frame.grid(row=0, column=0, sticky="w")
        
        # 세션 콤보박스
        self.session_combo = ttk.Combobox(
            self.session_frame,
            width=30,
            state="readonly"
        )
        self.session_combo.grid(row=0, column=0, padx=5)
        self.session_combo.bind("<<ComboboxSelected>>", self._on_session_change)
        
        # 세션 관리 버튼들
        self.new_session_btn = ttk.Button(
            self.session_frame,
            text="New Session",
            command=self._on_new_session
        )
        self.new_session_btn.grid(row=0, column=1, padx=2)
        
        self.rename_session_btn = ttk.Button(
            self.session_frame,
            text="Rename",
            command=self._on_rename_session
        )
        self.rename_session_btn.grid(row=0, column=2, padx=2)
        
        self.delete_session_btn = ttk.Button(
            self.session_frame,
            text="Delete",
            command=self._on_delete_session
        )
        self.delete_session_btn.grid(row=0, column=3, padx=2)
        
        # 설정 프레임
        self.settings_frame = ttk.Frame(self.toolbar)
        self.settings_frame.grid(row=0, column=1, sticky="e")
        
        # 테마 선택 콤보박스
        self.theme_combo = ttk.Combobox(
            self.settings_frame,
            values=list(self.theme_manager.DEFAULT_THEMES.keys()),
            state="readonly",
            width=10
        )
        self.theme_combo.set(self.current_theme)
        self.theme_combo.grid(row=0, column=0, padx=5)
        self.theme_combo.bind("<<ComboboxSelected>>", self._on_theme_change)
        
        # 폰트 크기 조절
        self.font_size_var = tk.StringVar(value=str(self.config.get('font_size', 10)))
        self.font_size_spinbox = ttk.Spinbox(
            self.settings_frame,
            from_=8,
            to=20,
            width=5,
            textvariable=self.font_size_var,
            command=self._on_font_size_change
        )
        self.font_size_spinbox.grid(row=0, column=1, padx=5)
        
    def _create_chat_area(self):
        """채팅 영역 생성"""
        self.chat_frame = ttk.Frame(self.main_frame)
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # 채팅 표시 영역
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            font=("TkDefaultFont", self.config.get('font_size', 10))
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew")
        self.chat_display.config(state=tk.DISABLED)
        
        # 채팅 영역 컨텍스트 메뉴
        self.chat_menu = self.context_menu_manager.create_chat_menu(self.chat_display)
        self.chat_display.bind("<Button-3>", lambda e: self.context_menu_manager.show_menu('chat', e))
        
    def _create_input_area(self):
        """입력 영역 생성"""
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        # 메시지 입력창
        self.input_box = tk.Text(
            self.input_frame,
            wrap=tk.WORD,
            height=3,
            font=("TkDefaultFont", self.config.get('font_size', 10))
        )
        self.input_box.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # 입력창 컨텍스트 메뉴
        self.input_menu = self.context_menu_manager.create_input_menu(self.input_box)
        self.input_box.bind("<Button-3>", lambda e: self.context_menu_manager.show_menu('input', e))
        
        # 버튼 프레임
        self.button_frame = ttk.Frame(self.input_frame)
        self.button_frame.grid(row=0, column=1, sticky="ns")
        
        # 전송 버튼
        self.send_btn = ttk.Button(
            self.button_frame,
            text="Send",
            command=self._on_send_message
        )
        self.send_btn.grid(row=0, column=0, pady=(0, 2))
        
        # 파일 첨부 버튼
        self.attach_btn = ttk.Button(
            self.button_frame,
            text="Attach",
            command=self._on_attach_file
        )
        self.attach_btn.grid(row=1, column=0)
        
    def _create_status_bar(self):
        """상태 표시줄 생성"""
        self.status_bar = ttk.Label(
            self.main_frame,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.grid(row=3, column=0, sticky="ew")
        
    def _setup_event_handlers(self):
        """이벤트 핸들러 설정"""
        # 메시지 관련 이벤트
        self.event_emitter.on(
            UIEventType.RECEIVE_MESSAGE.value,
            self._handle_received_message
        )
        self.event_emitter.on(
            UIEventType.MESSAGE_SENDING.value,
            self._handle_message_sending
        )
        self.event_emitter.on(
            UIEventType.MESSAGE_SENT.value,
            self._handle_message_sent
        )
        
        # 상태 변경 이벤트
        self.event_emitter.on(
            UIEventType.STATE_CHANGE.value,
            self._handle_state_change
        )
        
        # 에러 이벤트
        self.event_emitter.on(
            UIEventType.ERROR_OCCURRED.value,
            self._handle_error
        )
        
        # 경고 이벤트
        self.event_emitter.on(
            UIEventType.WARNING_OCCURRED.value,
            self._handle_warning
        )
        
    def _setup_key_bindings(self):
        """키보드 단축키 설정"""
        # 입력창 단축키
        self.input_box.bind("<Return>", self._on_return_key)
        self.input_box.bind("<Shift-Return>", self._on_shift_return)
        
        # 플랫폼별 단축키 설정
        is_mac = self.root.tk.call('tk', 'windowingsystem') == 'aqua'
        modifier = "Command" if is_mac else "Control"
        
        self.input_box.bind(f"<{modifier}-a>", self._on_select_all)
        self.input_box.bind(f"<{modifier}-A>", self._on_select_all)
        
    def _on_send_message(self, event=None):
        """메시지 전송"""
        if self.is_sending:
            return "break"
            
        message = self.input_box.get("1.0", tk.END).strip()
        if not message:
            return "break"
            
        self.event_emitter.emit(Event(
            UIEventType.SEND_MESSAGE.value,
            UIEventData.message(message)
        ))
        
        self.input_box.delete("1.0", tk.END)
        return "break"
        
    def _handle_received_message(self, data: dict):
        """메시지 수신 처리"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\nClaude: {data['content']}\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        self.status_bar.config(text="Ready")
        self.send_btn.config(state=tk.NORMAL)
        self.is_sending = False
        
    def _on_theme_change(self, event=None):
        """테마 변경"""
        new_theme = self.theme_combo.get()
        self.theme_manager.apply_theme(self.root, new_theme)
        self.current_theme = new_theme
        
        self.event_emitter.emit(Event(
            UIEventType.THEME_CHANGE.value,
            UIEventData.theme(new_theme)
        ))
        
    def _on_font_size_change(self):
        """폰트 크기 변경"""
        try:
            size = int(self.font_size_var.get())
            if 8 <= size <= 20:
                self.chat_display.config(font=("TkDefaultFont", size))
                self.input_box.config(font=("TkDefaultFont", size))
                
                self.event_emitter.emit(Event(
                    UIEventType.FONT_CHANGE.value,
                    {"size": size}
                ))
        except ValueError:
            pass
            
    def _on_return_key(self, event):
        """Enter 키 처리"""
        return self._on_send_message(event)
        
    def _on_shift_return(self, event):
        """Shift+Enter 키 처리"""
        self.input_box.insert(tk.INSERT, "\n")
        return "break"
        
    def _on_select_all(self, event):
        """전체 선택"""
        widget = event.widget
        widget.tag_add(tk.SEL, "1.0", tk.END)
        return "break"
        
    def _handle_error(self, data: dict):
        """에러 처리"""
        self.status_bar.config(text=f"Error: {data['message']}")
        
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\nError: {data['message']}\n", "error")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    def run(self):
        """UI 실행"""
        self.root.mainloop()
        
    def update_sessions(self, sessions: list):
        """세션 목록 업데이트"""
        current = self.session_combo.get()
        self.session_combo['values'] = sessions
        
        if current in sessions:
            self.session_combo.set(current)
        elif sessions:
            self.session_combo.set(sessions[0])