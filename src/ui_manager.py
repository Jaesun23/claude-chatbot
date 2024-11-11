import tkinter as tk
from tkinter import scrolledtext, filedialog, ttk, simpledialog, messagebox
from tkinter import font as tkfont
import platform
import asyncio
from typing import Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class UIManager:
    """사용자 인터페이스를 관리하는 클래스"""
    
    def __init__(self, master: tk.Tk, config: dict, conversation_manager: Any):
        """
        UI 매니저를 초기화합니다.
        
        Args:
            master: 메인 윈도우
            config: 설정 딕셔너리
            conversation_manager: 대화 관리자 인스턴스
        """
        self.master = master
        self.config = config
        self.conversation_manager = conversation_manager
        self.chat_app = None  # ChatApp 인스턴스는 나중에 설정됨
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.current_image = None
        
        # UI 생성
        self.create_widgets()
        self.apply_theme(config['theme'])
        self.update_font_size()
        self.update_window_title()
        self.bind_shortcuts()
        
        # 초기 세션 표시
        self.update_chat_display()
        
        logger.info("UI Manager initialized successfully")

    def create_widgets(self):
        """모든 UI 위젯을 생성하고 배치합니다."""
        # 기본 그리드 설정
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=1)

        self.create_settings_frame()
        self.create_chat_area()
        self.create_input_area()
        self.create_status_bar()

    def create_settings_frame(self):
        """설정 프레임을 생성합니다."""
        self.settings_frame = tk.Frame(self.master)
        self.settings_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.settings_frame.grid_columnconfigure(0, weight=1)

        # 버튼 프레임
        self.buttons_frame = tk.Frame(self.settings_frame)
        self.buttons_frame.grid(row=0, column=0, sticky="w")

        # 테마 버튼
        self.theme_button = tk.Button(
            self.buttons_frame,
            text="Light Mode" if self.config['theme'] == 'dark' else "Dark Mode",
            command=self.toggle_theme
        )
        self.theme_button.grid(row=0, column=0, padx=5, pady=2)

        # 폰트 크기 설정
        self.font_size_label = tk.Label(self.buttons_frame, text="Font Size:")
        self.font_size_label.grid(row=0, column=1, padx=5, pady=2)

        self.font_size_var = tk.StringVar(value=str(self.config['font_size']))
        self.font_size_entry = tk.Entry(
            self.buttons_frame,
            textvariable=self.font_size_var,
            width=3
        )
        self.font_size_entry.grid(row=0, column=2, padx=5, pady=2)
        self.font_size_entry.bind('<Return>', self.update_font_size)

        # 대화 저장 버튼
        self.save_button = tk.Button(
            self.buttons_frame,
            text="Save Chat",
            command=self.save_chat
        )
        self.save_button.grid(row=0, column=3, padx=5, pady=2)

        # 세션 관리 프레임
        self.create_session_frame()

    def create_session_frame(self):
        """세션 관리 프레임을 생성합니다."""
        self.session_frame = tk.Frame(self.settings_frame)
        self.session_frame.grid(row=1, column=0, sticky="w", pady=2)

        # 세션 선택 콤보박스
        self.session_combo = ttk.Combobox(
            self.session_frame,
            values=self.conversation_manager.list_sessions()
        )
        self.session_combo.grid(row=0, column=0, padx=5)
        
        # 현재 세션 설정
        current_session = self.conversation_manager.current_session
        if current_session:
            self.session_combo.set(current_session)
        
        self.session_combo.bind("<<ComboboxSelected>>", self.change_session)

        # 세션 관리 버튼들
        self.new_session_button = tk.Button(
            self.session_frame,
            text="New Session",
            command=self.new_session
        )
        self.new_session_button.grid(row=0, column=1, padx=5)

        self.rename_button = tk.Button(
            self.session_frame,
            text="Rename Session",
            command=self.rename_session
        )
        self.rename_button.grid(row=0, column=2, padx=5)

        self.delete_button = tk.Button(
            self.session_frame,
            text="Delete Session",
            command=self.delete_session
        )
        self.delete_button.grid(row=0, column=3, padx=5)

    def create_chat_area(self):
        """채팅 영역을 생성합니다."""
        self.chat_box = scrolledtext.ScrolledText(
            self.master,
            wrap=tk.WORD,
            width=60,
            height=20
        )
        self.chat_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.chat_box.config(state=tk.DISABLED)

        # 마우스 우클릭 메뉴
        self.chat_box_context_menu = tk.Menu(self.chat_box, tearoff=0)
        self.chat_box_context_menu.add_command(label="Copy", command=self.copy_chat)
        self.chat_box.bind("<Button-3>", self.show_chat_context_menu)

    def create_input_area(self):
        """입력 영역을 생성합니다."""
        self.input_frame = tk.Frame(self.master)
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.input_frame.grid_columnconfigure(0, weight=1)

        # 입력 창
        self.input_box = tk.Text(
            self.input_frame,
            wrap=tk.WORD,
            height=3
        )
        self.input_box.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.input_box.bind("<Return>", self.handle_return)
        self.input_box.bind("<Shift-Return>", self.insert_newline)
        self.input_box.focus_set()

        # 전송 버튼
        button_height = self.input_box.winfo_reqheight() // 2
        self.send_button = tk.Button(
            self.input_frame,
            text="Send",
            command=self.send_message,
            height=1
        )
        self.send_button.grid(row=0, column=1, padx=(5, 0), pady=(0, 2))

        # 이미지 첨부 버튼
        self.attach_button = tk.Button(
            self.input_frame,
            text="Attach",
            command=self.attach_file,
            height=1
        )
        self.attach_button.grid(row=1, column=1, padx=(5, 0), pady=(2, 0))

    def create_status_bar(self):
        """상태 바를 생성합니다."""
        self.status_bar = tk.Label(
            self.master,
            text="Ready",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.grid(row=3, column=0, sticky="ew")

    async def send_message(self, event=None):
        """
        메시지를 전송합니다.
        
        Args:
            event: 이벤트 객체 (키보드 이벤트 등)
        """
        if event and event.state & 0x1:  # Shift key pressed
            return self.insert_newline(event)

        message = self.input_box.get("1.0", tk.END).strip()
        if not message and not self.current_image:
            return "break"

        self.input_box.delete("1.0", tk.END)
        self.set_status("Sending message...")

        try:
            current_session = self.conversation_manager.get_current_session()
            
            if self.current_image:
                response = await current_session.process_image_message(
                    message,
                    self.current_image
                )
                self.current_image = None
                self.update_image_label()
            else:
                response = await current_session.get_response(message)

            self.display_message("You", message)
            await self.display_response(response)
            self.set_status("Ready")
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}", exc_info=True)
            self.show_error(f"메시지 전송 중 오류 발생: {str(e)}")
            self.set_status("Error occurred")

        return "break"

    async def display_response(self, response: str):
        """
        Claude의 응답을 점진적으로 표시합니다.
        
        Args:
            response: 표시할 응답 텍스트
        """
        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.insert(tk.END, "Claude: ")
        
        for char in response:
            self.chat_box.insert(tk.END, char)
            self.chat_box.see(tk.END)
            self.chat_box.update_idletasks()
            await asyncio.sleep(0.001)  # 타이핑 효과를 위한 짧은 딜레이
            
        self.chat_box.insert(tk.END, "\n\n")
        self.chat_box.config(state=tk.DISABLED)
        self.chat_box.see(tk.END)

    def handle_return(self, event):
        """Return 키 입력을 처리합니다."""
        asyncio.run(self.send_message(event))
        return "break"

    def apply_theme(self, theme: str):
        """
        테마를 적용합니다.
        
        Args:
            theme: 적용할 테마 ('dark' 또는 'light')
        """
        colors = {
            'dark': {
                'bg': '#2b2b2b',
                'fg': 'white',
                'input_bg': '#383838',
                'button_bg': '#404040',
                'button_fg': 'white'
            },
            'light': {
                'bg': 'white',
                'fg': 'black',
                'input_bg': '#f0f0f0',
                'button_bg': '#e0e0e0',
                'button_fg': 'black'
            }
        }[theme]

        # 위젯들에 색상 적용
        self.master.configure(bg=colors['bg'])
        self.chat_box.config(bg=colors['bg'], fg=colors['fg'])
        self.input_box.config(bg=colors['input_bg'], fg=colors['fg'])
        
        for frame in [self.settings_frame, self.buttons_frame, 
                     self.session_frame, self.input_frame]:
            frame.config(bg=colors['bg'])
            
        for button in [self.send_button, self.attach_button,
                      self.new_session_button, self.rename_button,
                      self.delete_button, self.save_button]:
            button.config(bg=colors['button_bg'], fg=colors['button_fg'])
            
        self.theme_button.config(
            text='Light Mode' if theme == 'dark' else 'Dark Mode',
            bg=colors['button_bg'],
            fg=colors['button_fg']
        )
        
        for label in [self.font_size_label, self.status_bar]:
            label.config(bg=colors['bg'], fg=colors['fg'])

    def show_error(self, message: str):
        """
        에러 메시지를 표시합니다.
        
        Args:
            message: 표시할 에러 메시지
        """
        logger.error(message)
        messagebox.showerror("Error", message)

    def show_info(self, message: str):
        """
        정보 메시지를 표시합니다.
        
        Args:
            message: 표시할 정보 메시지
        """
        logger.info(message)
        messagebox.showinfo("Information", message)

    def set_status(self, message: str):
        """
        상태 바 메시지를 업데이트합니다.
        
        Args:
            message: 표시할 상태 메시지
        """
        self.status_bar.config(text=message)