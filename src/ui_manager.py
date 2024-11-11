import tkinter as tk
from tkinter import scrolledtext, filedialog, ttk, simpledialog, messagebox
import os
import asyncio
from typing import Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor
import threading
from config_manager import ConfigManager

class UIManager:
# 1. 초기화와 기본 UI 설정 관련
    def __init__(self, master: tk.Tk, config: dict, session_manager: Any):
        """
        UI 관리자를 초기화합니다.

        Args:
            master: 메인 윈도우
            config: 설정 딕셔너리
            session_manager: 세션 관리자 인스턴스
        """
        self.master = master
        self.config = config
        self.session_manager = session_manager
        self.chat_app = None  # ChatApp 인스턴스는 나중에 설정됨
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.create_widgets()
        
    def create_widgets(self):
        """UI 위젯들을 생성하고 배치합니다."""
        # 기본 그리드 설정
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=1)

        # 상단 설정 프레임
        self.create_settings_frame()
        
        # 대화 영역
        self.create_chat_area()
        
        # 입력 영역
        self.create_input_area()
        
        # 상태 바
        self.create_status_bar()
        
        # 단축키 바인딩
        self.bind_shortcuts()

    def create_settings_frame(self):
        """상단 설정 영역을 생성합니다."""
        self.settings_frame = tk.Frame(self.master)
        self.settings_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.settings_frame.grid_columnconfigure(0, weight=1)

        # 버튼 프레임
        self.buttons_frame = tk.Frame(self.settings_frame)
        self.buttons_frame.grid(row=0, column=0, sticky="w")

        # 테마 버튼
        self.theme_button = tk.Button(self.buttons_frame, 
                                    text="Light Mode", 
                                    command=self.toggle_theme)
        self.theme_button.grid(row=0, column=0, padx=5, pady=2)

        # 폰트 크기 설정
        self.font_size_label = tk.Label(self.buttons_frame, text="Font Size:")
        self.font_size_label.grid(row=0, column=1, padx=5, pady=2)

        self.font_size_var = tk.StringVar(value=str(self.config['font_size']))
        self.font_size_entry = tk.Entry(self.buttons_frame, 
                                      textvariable=self.font_size_var, 
                                      width=3)
        self.font_size_entry.grid(row=0, column=2, padx=5, pady=2)
        self.font_size_entry.bind('<Return>', self.update_font_size)

        # 대화 저장 버튼
        self.save_button = tk.Button(self.buttons_frame, 
                                   text="Save Chat", 
                                   command=self.save_chat)
        self.save_button.grid(row=0, column=3, padx=5, pady=2)

        # 세션 프레임
        self.create_session_frame()
        
        # 컨텍스트 프레임
        self.create_context_frame()

    def create_session_frame(self):
        """세션 관리 프레임을 생성합니다."""
        self.session_frame = tk.Frame(self.settings_frame)
        self.session_frame.grid(row=1, column=0, sticky="w", pady=2)

        # 세션 콤보박스
        self.session_combo = ttk.Combobox(
            self.session_frame, 
            values=self.session_manager.list_sessions()
        )
        self.session_combo.grid(row=0, column=0, padx=5)
        
        # 현재 세션이 있으면 선택
        if self.session_manager.current_session:
            self.session_combo.set(self.session_manager.current_session)
        
        # 콤보박스 선택 이벤트 바인딩
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

    def create_context_frame(self):
        """컨텍스트 관리 프레임을 생성합니다."""
        self.context_frame = tk.Frame(self.settings_frame)
        self.context_frame.grid(row=2, column=0, sticky="w", pady=2)

        self.context_label = tk.Label(self.context_frame, text="Context:")
        self.context_label.grid(row=0, column=0, padx=5)

        self.context_combo = ttk.Combobox(
            self.context_frame,
            values=self.get_current_session().get_available_contexts()
        )
        self.context_combo.set("general")
        self.context_combo.grid(row=0, column=1, padx=5)
        self.context_combo.bind("<<ComboboxSelected>>", self.change_context)

        self.add_context_button = tk.Button(
            self.context_frame,
            text="Add Custom Context",
            command=self.add_custom_context
        )
        self.add_context_button.grid(row=0, column=2, padx=5)

    def create_chat_area(self):
        """대화 영역을 생성합니다."""
        self.chat_box = scrolledtext.ScrolledText(
            self.master,
            wrap=tk.WORD,
            width=60,
            height=20
        )
        self.chat_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.chat_box.config(state=tk.DISABLED)

    def create_input_area(self):
        """입력 영역을 생성합니다."""
        self.input_frame = tk.Frame(self.master)
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.input_frame.grid_columnconfigure(0, weight=1)

        # 텍스트 입력 영역
        self.input_box = tk.Text(
            self.input_frame,
            wrap=tk.WORD,
            height=3
        )
        self.input_box.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.input_box.bind("<Return>", self.send_message)
        self.input_box.bind("<Shift-Return>", self.insert_newline)
        self.input_box.focus_set()

        button_size = self.input_box.winfo_reqheight()

        # 전송 버튼
        self.send_button = tk.Button(
            self.input_frame,
            text="Send",
            command=lambda: asyncio.run(self.send_message())
        )
        self.send_button.grid(row=0, column=1, padx=(5, 0), pady=(0, 2))

        # 이미지 업로드 버튼
        self.image_button = tk.Button(
            self.input_frame,
            text="Upload Image",
            command=self.upload_image
        )
        self.image_button.grid(row=1, column=1, padx=(5, 0), pady=(2, 0))

        # 현재 선택된 이미지 표시 라벨
        self.image_label = tk.Label(
            self.input_frame,
            text="No image selected"
        )
        self.image_label.grid(row=2, column=0, columnspan=2, pady=2)

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


# 2. 테마와 폰트 관련
    def apply_theme(self, theme):
        """
        지정된 테마를 적용합니다.
        
        Args:
            theme (str): 적용할 테마 ('dark' 또는 'light')
        """
        if theme == 'dark':
            bg_color = '#2b2b2b'
            fg_color = 'white'
            input_bg = '#383838'
            button_bg = '#404040'
            button_fg = 'white'
        else:
            bg_color = 'white'
            fg_color = 'black'
            input_bg = '#f0f0f0'
            button_bg = '#e0e0e0'
            button_fg = 'black'

        # 메인 윈도우 색상 설정
        self.master.configure(bg=bg_color)
        
        # 채팅 영역 색상 설정
        self.chat_box.config(bg=bg_color, fg=fg_color)
        
        # 입력 영역 색상 설정
        self.input_box.config(bg=input_bg, fg=fg_color)
        self.input_frame.config(bg=bg_color)
        
        # 버튼들의 색상 설정
        for button in [self.send_button, self.image_button, 
                    self.new_session_button, self.rename_button, 
                    self.delete_button, self.save_button, 
                    self.theme_button, self.add_context_button]:
            button.config(bg=button_bg, fg=button_fg)
            
        # 프레임들의 배경색 설정
        for frame in [self.settings_frame, self.buttons_frame, 
                    self.session_frame, self.context_frame]:
            frame.config(bg=bg_color)
            
        # 라벨들의 색상 설정
        for label in [self.font_size_label, self.context_label, 
                    self.image_label, self.status_bar]:
            label.config(bg=bg_color, fg=fg_color)
            
        # 테마 버튼 텍스트 업데이트
        self.theme_button.config(text='Light Mode' if theme == 'dark' else 'Dark Mode')

    def toggle_theme(self):
        """테마를 다크/라이트 모드로 전환합니다."""
        new_theme = 'light' if self.config['theme'] == 'dark' else 'dark'
        self.config['theme'] = new_theme
        self.apply_theme(new_theme)
        ConfigManager.save_config(self.config)

    def update_font_size(self, event=None):
        """
        폰트 크기를 업데이트합니다.
        
        Args:
            event: 이벤트 객체 (바인딩된 이벤트에서 호출될 때 사용)
        """
        try:
            new_size = int(self.font_size_var.get())
            if 8 <= new_size <= 20:  # 폰트 크기 범위 제한
                self.config['font_size'] = new_size
                font = ('TkDefaultFont', new_size)
                
                # 채팅창과 입력창의 폰트 크기 업데이트
                self.chat_box.config(font=font)
                self.input_box.config(font=font)
                
                # 설정 저장
                ConfigManager.save_config(self.config)
        except ValueError:
            # 숫자가 아닌 값이 입력된 경우
            self.font_size_var.set(str(self.config['font_size']))


# 3. 세션 관리 관련
    def change_session(self, event=None):
        """
        선택된 세션으로 전환합니다.

        Args:
            event: 이벤트 객체 (콤보박스 선택 이벤트에서 호출될 때 사용)
        """
        selected_session = self.session_combo.get()
        try:
            # 세션 매니저의 세션 전환
            self.session_manager.switch_session(selected_session)
            
            # 대화 내용 업데이트
            self.update_chat_display()
            
            # 상태 업데이트
            self.set_status(f"Switched to session: {selected_session}")
            
            # 컨텍스트 콤보박스 업데이트 (컨텍스트 기능을 사용하는 경우)
            if hasattr(self, 'context_combo'):
                current_session = self.session_manager.get_current_session()
                self.context_combo['values'] = current_session.get_available_contexts()
                self.context_combo.set(current_session.context_manager.active_context)
                
        except Exception as e:
            self.show_error(f"Failed to change session: {str(e)}")

    def new_session(self):
        """새 세션을 생성합니다."""
        new_session_name = simpledialog.askstring("New Session", "Enter a name for the new session:")
        if new_session_name:
            try:
                self.session_manager.create_new_session(new_session_name)
                self.session_combo['values'] = self.session_manager.list_sessions()
                self.session_combo.set(new_session_name)
                self.change_session()
            except Exception as e:
                self.show_error(f"Failed to create new session: {str(e)}")

    def rename_session(self):
        """현재 세션의 이름을 변경합니다."""
        if not self.session_manager.current_session:
            self.show_error("No session selected")
            return
            
        current_name = self.session_manager.current_session
        new_name = simpledialog.askstring(
            "Rename Session", 
            "Enter new session name:",
            initialvalue=current_name
        )
        
        if new_name:
            try:
                self.session_manager.rename_session(new_name)
                self.session_combo['values'] = self.session_manager.list_sessions()
                self.session_combo.set(new_name)
            except Exception as e:
                self.show_error(f"Failed to rename session: {str(e)}")

    def delete_session(self):
        """현재 세션을 삭제합니다."""
        if not self.session_manager.current_session:
            self.show_error("No session selected")
            return
            
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this session?"):
            try:
                self.session_manager.delete_session()
                self.session_combo['values'] = self.session_manager.list_sessions()
                self.session_combo.set(self.session_manager.current_session)
                self.update_chat_display()
            except Exception as e:
                self.show_error(f"Failed to delete session: {str(e)}")

    def update_chat_display(self):
        """대화창의 내용을 현재 세션의 내용으로 업데이트합니다."""
        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.delete("1.0", tk.END)
        
        current_session = self.session_manager.get_current_session()
        if current_session and current_session.messages:
            for message in current_session.messages:
                role = self.config['user_name'] if message["role"] == "user" else "Claude"
                self.chat_box.insert(tk.END, f"{role}: {message['content']}\n\n")
        
        self.chat_box.config(state=tk.DISABLED)
        self.chat_box.see(tk.END)


# 4. 채팅 UI 업데이트 관련        
    def display_message(self, sender: str, message: str):
        """메시지를 대화창에 표시합니다."""
        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.insert(tk.END, f"\n{sender}: {message}\n")
        self.chat_box.config(state=tk.DISABLED)
        self.chat_box.see(tk.END)

    def display_system_message(self, message: str):
        """시스템 메시지를 대화창에 표시합니다."""
        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.insert(tk.END, f"\nSystem: {message}\n")
        self.chat_box.config(state=tk.DISABLED)
        self.chat_box.see(tk.END)

    def set_status(self, message: str):
        """상태 바 메시지를 업데이트합니다."""
        self.status_bar.config(text=message)


# 5. 파일과 이미지 처리 관련
    def save_chat(self):
        """대화 내용을 파일로 저장합니다."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(self.chat_box.get("1.0", tk.END))
                self.show_info(f"Chat saved to: {file_path}")
            except Exception as e:
                self.show_error(f"Failed to save chat: {str(e)}")

    def upload_image(self):
        """이미지 파일을 업로드합니다."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.webp")]
        )
        
        if file_path:
            try:
                self.current_image = file_path
                filename = os.path.basename(file_path)
                self.image_label.config(text=f"Selected: {filename}")
            except Exception as e:
                self.show_error(f"Image upload failed: {str(e)}")


# 6. 단축키와 이벤트 처리 관련
    def bind_shortcuts(self):
        """키보드 단축키를 바인딩합니다."""
        # 플랫폼에 따른 단축키 설정
        is_mac = self.master.tk.call('tk', 'windowingsystem') == 'aqua'
        modifier = 'Command' if is_mac else 'Control'

        # 입력 영역 단축키
        self.input_box.bind(f"<{modifier}-Return>", self.send_message)
        self.input_box.bind(f"<{modifier}-v>", self.paste)
        self.input_box.bind(f"<{modifier}-c>", self.copy)
        self.input_box.bind(f"<{modifier}-x>", self.cut)
        self.input_box.bind(f"<{modifier}-a>", self.select_all)

        # 대화 영역 단축키
        self.chat_box.bind(f"<{modifier}-c>", self.copy_chat)

    def copy(self, event=None):
        """선택된 텍스트를 복사합니다."""
        try:
            self.master.clipboard_clear()
            selected = self.input_box.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.master.clipboard_append(selected)
        except tk.TclError:
            pass
        return "break"

    def paste(self, event=None):
        """클립보드의 내용을 붙여넣습니다."""
        try:
            text = self.master.clipboard_get()
            self.input_box.insert(tk.INSERT, text)
        except tk.TclError:
            pass
        return "break"

    def cut(self, event=None):
        """선택된 텍스트를 잘라냅니다."""
        self.copy()
        try:
            self.input_box.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass
        return "break"

    def select_all(self, event=None):
        """모든 텍스트를 선택합니다."""
        self.input_box.tag_add(tk.SEL, "1.0", tk.END)
        return "break"

    def copy_chat(self, event=None):
        """채팅창의 선택된 텍스트를 복사합니다."""
        try:
            self.master.clipboard_clear()
            selected = self.chat_box.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.master.clipboard_append(selected)
        except tk.TclError:
            pass
        return "break"

    def insert_newline(self, event):
        """새로운 줄을 삽입합니다."""
        self.input_box.insert(tk.INSERT, '\n')
        return "break"

    async def send_message(self, event=None):
        """메시지를 전송합니다."""
        if event and event.state & 0x1:  # Shift key pressed
            return self.insert_newline(event)

        message = self.input_box.get("1.0", tk.END).strip()
        if not message and not hasattr(self, 'current_image'):
            return "break"

        self.input_box.delete("1.0", tk.END)
        self.set_status("Sending message...")
        
        try:
            current_session = self.get_current_session()
            
            if hasattr(self, 'current_image'):
                response = await current_session.process_image_message(
                    message,
                    self.current_image
                )
                delattr(self, 'current_image')
                self.image_label.config(text="No image selected")
            else:
                response = await current_session.get_response(message)

            self.display_message("You", message)
            self.display_message("Claude", response)
            self.set_status("Ready")
            
        except Exception as e:
            self.show_error(f"Message sending failed: {str(e)}")
            self.set_status("Error occurred")

        return "break"


# 7. 컨텍스트 관리 관련
    def change_context(self, event=None):
        """컨텍스트를 변경합니다."""
        selected_context = self.context_combo.get()
        try:
            current_session = self.get_current_session()
            prompt = current_session.change_context(selected_context)
            self.display_system_message(f"Changed context to: {selected_context}")
        except Exception as e:
            self.show_error(f"Context change failed: {str(e)}")

    def add_custom_context(self):
        """커스텀 컨텍스트를 추가합니다."""
        dialog = CustomContextDialog(self.master)
        if dialog.result:
            name, prompt = dialog.result
            try:
                self.get_current_session().add_custom_context(name, prompt)
                self.update_context_list()
                self.show_info(f"Added new context: {name}")
            except Exception as e:
                self.show_error(f"Failed to add context: {str(e)}")

    def update_context_list(self):
        """컨텍스트 목록을 업데이트합니다."""
        current_contexts = self.get_current_session().get_available_contexts()
        self.context_combo['values'] = current_contexts

    def get_current_session(self):
        """현재 활성화된 세션을 반환합니다."""
        return self.session_manager.sessions[self.session_manager.current_session]


# 8. 유틸리티 메소드
    def show_error(self, message: str):
        """에러 메시지를 표시합니다."""
        messagebox.showerror("Error", message)

    def show_info(self, message: str):
        """정보 메시지를 표시합니다."""
        messagebox.showinfo("Information", message)



class CustomContextDialog:
    """커스텀 컨텍스트 추가를 위한 다이얼로그"""
    def __init__(self, parent):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Custom Context")
        self.create_widgets()
        
        self.dialog.transient(parent)
        self.dialog.grab_set()
        parent.wait_window(self.dialog)

    def create_widgets(self):
        """다이얼로그 위젯을 생성합니다."""
        # 이름 입력
        tk.Label(self.dialog, text="Context Name:").grid(row=0, column=0, padx=5, pady=5)
        self.name_entry = tk.Entry(self.dialog)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 프롬프트 입력
        tk.Label(self.dialog, text="System Prompt:").grid(row=1, column=0, padx=5, pady=5)
        self.prompt_text = tk.Text(self.dialog, height=4, width=40)
        self.prompt_text.grid(row=1, column=1, padx=5, pady=5)
        
        # 버튼
        button_frame = tk.Frame(self.dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        tk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)

    def ok(self):
        """확인 버튼의 동작을 처리합니다."""
        name = self.name_entry.get().strip()
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        
        if name and prompt:
            self.result = (name, prompt)
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", "Please fill in all fields")

    def cancel(self):
        """취소 버튼의 동작을 처리합니다."""
        self.dialog.destroy()