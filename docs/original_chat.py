import tkinter as tk
from tkinter import scrolledtext, filedialog, ttk, simpledialog, messagebox
from tkinter import font as tkfont
import anthropic
import os
import json
import time
import base64
import platform
import sys

class APIKeyManager:
    @staticmethod
    def get_api_key():
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다. zshrc 파일을 확인해주세요.")
        return api_key

class ConfigManager:
    CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'chat_config.json')
    DEFAULT_CONFIG = {
        'window_size': '800x600',
        'theme': 'dark',
        'font_size': 10,
        'user_name': 'Jason'
    }

    @classmethod
    def load_config(cls):
        try:
            if os.path.exists(cls.CONFIG_FILE):
                with open(cls.CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except json.JSONDecodeError:
            messagebox.showerror("Error", "설정 파일 형식이 올바르지 않습니다. 기본 설정을 사용합니다.")
        except IOError as e:
            messagebox.showerror("Error", f"설정 파일을 읽는 중 오류가 발생했습니다: {e}")
        return cls.DEFAULT_CONFIG

    @classmethod
    def save_config(cls, config):
        try:
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except IOError as e:
            messagebox.showerror("Error", f"설정 파일을 저장하는 중 오류가 발생했습니다: {e}")
class ChatSession:
    def __init__(self, name, messages=None):
        self.name = name
        self.messages = messages if messages is not None else []

    def add_message(self, role, content):
        if role in ["user", "assistant"] and isinstance(content, str):
            self.messages.append({"role": role, "content": content})
        else:
            raise ValueError("Invalid role or content type.")

class SessionManager:
    SESSIONS_FILE = os.path.join(os.path.dirname(__file__), 'chat_sessions.json')

    def __init__(self):
        self.sessions = self.load_sessions()
        self.current_session = 0

    def load_sessions(self):
        try:
            if os.path.exists(self.SESSIONS_FILE):
                with open(self.SESSIONS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return [ChatSession(session_data['name'], session_data['messages']) for session_data in data]
            else:
                return [ChatSession("New Session")]
        except json.JSONDecodeError:
            messagebox.showerror("Error", "세션 파일 형식이 올바르지 않습니다. 새 세션을 시작합니다.")
        except IOError as e:
            messagebox.showerror("Error", f"세션 파일을 읽는 중 오류가 발생했습니다: {e}")
        return [ChatSession("New Session")]

    def save_sessions(self):
        try:
            data = [{'name': session.name, 'messages': session.messages} for session in self.sessions]
            with open(self.SESSIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            messagebox.showerror("Error", f"세션을 저장하는 중 오류가 발생했습니다: {e}")

    def new_session(self, name):
        self.sessions.append(ChatSession(name))
        self.current_session = len(self.sessions) - 1

    def change_session(self, index):
        if 0 <= index < len(self.sessions):
            self.current_session = index

    def rename_session(self, new_name):
        self.sessions[self.current_session].name = new_name

    def delete_session(self):
        if len(self.sessions) > 1:
            del self.sessions[self.current_session]
            self.current_session = 0
        else:
            messagebox.showerror("Error", "You must have at least one session.")

class RoundedButton(tk.Canvas):
    def __init__(self, parent, width, height, cornerradius, padding, color, text, command=None):
        super().__init__(parent, borderwidth=0, relief="flat", highlightthickness=0, bg=parent["bg"])
        self.command = command

        if cornerradius > 0.5 * width:
            cornerradius = 0.5 * width
        if cornerradius > 0.5 * height:
            cornerradius = 0.5 * height

        rad = 2 * cornerradius
        def shape():
            self.create_polygon((padding, height - cornerradius - padding, padding, cornerradius + padding, padding + cornerradius, padding, width - padding - cornerradius, padding, width - padding, cornerradius + padding, width - padding, height - cornerradius - padding, width - padding - cornerradius, height - padding, padding + cornerradius, height - padding), fill=color, outline=color, tags=("button",))
            self.create_arc((padding, padding + rad, padding + rad, padding), start=90, extent=90, fill=color, outline=color, tags=("button",))
            self.create_arc((width - padding - rad, padding, width - padding, padding + rad), start=0, extent=90, fill=color, outline=color, tags=("button",))
            self.create_arc((width - padding, height - rad - padding, width - padding - rad, height - padding), start=270, extent=90, fill=color, outline=color, tags=("button",))
            self.create_arc((padding, height - padding - rad, padding + rad, height - padding), start=180, extent=90, fill=color, outline=color, tags=("button",))

        shape()
        self.text_item = self.create_text(width / 2, height / 2, text=text, fill='black', tags=("text",))
        self.configure(width=width, height=height)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_press(self, event):
        self.configure(relief="sunken")

    def _on_release(self, event):
        self.configure(relief="raised")
        if self.command is not None:
            self.command()

    def configure(self, **kwargs):
        bg = kwargs.pop('bg', None)
        fg = kwargs.pop('fg', None)
        if bg:
            self.itemconfig("button", fill=bg, outline=bg)
        if fg:
            self.itemconfig("text", fill=fg)
        super().configure(**kwargs)

class CodeBlock(tk.Frame):
    def __init__(self, master, code, language):
        super().__init__(master, bg='#2b2b2b', bd=1, relief='solid')
        self.code = code
        self.language = language

        # Header
        header = tk.Frame(self, bg='#1e1e1e')
        header.pack(fill='x')

        # Language label
        lang_label = tk.Label(header, text=language, bg='#1e1e1e', fg='#d4d4d4')
        lang_label.pack(side='left', padx=5)

        # Copy button
        copy_btn = tk.Button(header, text="Copy", command=self.copy_code, bg='#3c3c3c', fg='#d4d4d4')
        copy_btn.pack(side='right', padx=5, pady=2)

        # Code text
        code_font = tkfont.Font(family="Courier", size=10)
        self.code_text = tk.Text(self, wrap='none', bg='#1e1e1e', fg='#d4d4d4', font=code_font, height=10)
        self.code_text.pack(expand=True, fill='both')
        self.code_text.insert('1.0', code)
        self.code_text.config(state='disabled')

        # Scrollbar
        scrollbar = tk.Scrollbar(self, command=self.code_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.code_text.config(yscrollcommand=scrollbar.set)

    def copy_code(self):
        self.master.clipboard_clear()
        self.master.clipboard_append(self.code)

class UIManager:
    def __init__(self, master, config, session_manager):
        self.master = master
        self.config = config
        self.session_manager = session_manager
        self.create_widgets()
        self.apply_theme(config['theme'])
        self.update_font_size()
        self.update_window_title()
        self.bind_shortcuts()

    def create_widgets(self):
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=1)

        self.settings_frame = tk.Frame(self.master)
        self.settings_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.settings_frame.grid_columnconfigure(0, weight=1)

        self.buttons_frame = tk.Frame(self.settings_frame)
        self.buttons_frame.grid(row=0, column=0, sticky="w")

        self.theme_button = tk.Button(self.buttons_frame, text="Light Mode", command=self.toggle_theme)
        self.theme_button.grid(row=0, column=0, padx=5, pady=2)

        self.font_size_label = tk.Label(self.buttons_frame, text="Font Size:")
        self.font_size_label.grid(row=0, column=1, padx=5, pady=2)

        self.font_size_var = tk.StringVar(value=str(self.config['font_size']))
        self.font_size_entry = tk.Entry(self.buttons_frame, textvariable=self.font_size_var, width=3)
        self.font_size_entry.grid(row=0, column=2, padx=5, pady=2)
        self.font_size_entry.bind('<Return>', self.update_font_size)

        self.save_button = tk.Button(self.buttons_frame, text="Save Chat", command=self.save_chat)
        self.save_button.grid(row=0, column=3, padx=5, pady=2)

        self.session_frame = tk.Frame(self.settings_frame)
        self.session_frame.grid(row=1, column=0, sticky="w", pady=2)

        self.session_combo = ttk.Combobox(self.session_frame, values=[s.name for s in self.session_manager.sessions])
        self.session_combo.grid(row=0, column=0, padx=5)
        self.session_combo.set(self.session_manager.sessions[0].name)
        self.session_combo.bind("<<ComboboxSelected>>", self.change_session)

        self.new_session_button = tk.Button(self.session_frame, text="New Session", command=self.new_session)
        self.new_session_button.grid(row=0, column=1, padx=5)

        self.rename_button = tk.Button(self.session_frame, text="Rename Session", command=self.rename_session)
        self.rename_button.grid(row=0, column=2, padx=5)

        self.delete_button = tk.Button(self.session_frame, text="Delete Session", command=self.delete_session)
        self.delete_button.grid(row=0, column=3, padx=5)

        self.chat_box = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, width=60, height=20)
        self.chat_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.chat_box.config(state=tk.DISABLED)

        self.input_frame = tk.Frame(self.master)
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.input_box = tk.Text(self.input_frame, wrap=tk.WORD, height=3)
        self.input_box.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.input_box.bind("<Return>", self.send_message)
        self.input_box.bind("<Shift-Return>", self.insert_newline)
        self.input_box.focus_set()

        button_size = self.input_box.winfo_reqheight()

        self.send_button = RoundedButton(self.input_frame, width=80, height=button_size, 
                                         cornerradius=3, padding=4, color='#A9A9A9', 
                                         text="Send", command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=(5, 0), pady=(0, 2))

        self.attach_button = RoundedButton(self.input_frame, width=80, height=button_size, 
                                           cornerradius=3, padding=4, color='#A9A9A9', 
                                           text="Attach", command=self.attach_file)
        self.attach_button.grid(row=1, column=1, padx=(5, 0), pady=(2, 0))

        self.attached_file = None

    def apply_theme(self, theme):
        if theme == 'dark':
            button_bg, button_fg, bg_color, fg_color, input_bg = '#A9A9A9', 'black', '#2b2b2b', 'white', '#383838'
        else:
            button_bg, button_fg, bg_color, fg_color, input_bg = '#f0f0f0', 'black', 'white', 'black', '#f0f0f0'

        self.master.configure(bg=bg_color)
        self.chat_box.config(bg=bg_color, fg=fg_color)
        self.input_box.config(bg=input_bg, fg=fg_color)
        self.send_button.configure(bg=button_bg, fg=button_fg)
        self.theme_button.config(text='Light Mode' if theme == 'dark' else 'Dark Mode', bg=button_bg, fg=button_fg)
        for widget in [self.save_button, self.new_session_button, self.rename_button, self.delete_button]:
            widget.config(bg=button_bg, fg=button_fg)
        self.settings_frame.config(bg=bg_color)
        self.buttons_frame.config(bg=bg_color)
        self.session_frame.config(bg=bg_color)
        self.input_frame.config(bg=bg_color)
        self.font_size_label.config(bg=bg_color, fg=fg_color)

    def update_font_size(self, event=None):
        try:
            new_size = int(self.font_size_var.get())
            if 8 <= new_size <= 20:
                self.config['font_size'] = new_size
                font = ('TkDefaultFont', new_size)
                self.chat_box.config(font=font)
                self.input_box.config(font=font)
        except ValueError:
            pass

    def update_window_title(self):
        self.master.title(f"Chat with Claude - {self.session_manager.sessions[self.session_manager.current_session].name}")

    def bind_shortcuts(self):
        if platform.system() == "Darwin":  # macOS
            self.input_box.bind("<Command-x>", self.cut)
            self.input_box.bind("<Command-c>", self.copy)
            self.input_box.bind("<Command-v>", self.paste)
            self.input_box.bind("<Command-a>", self.select_all)
            self.chat_box.bind("<Command-c>", self.copy_chat_box)
            self.master.bind_class("Text", "<Command-x>", self.cut)
            self.master.bind_class("Text", "<Command-c>", self.copy)
            self.master.bind_class("Text", "<Command-v>", self.paste)
            self.master.bind_class("Text", "<Command-a>", self.select_all)
        else:  # Windows/Linux
            self.input_box.bind("<Control-x>", self.cut)
            self.input_box.bind("<Control-c>", self.copy)
            self.input_box.bind("<Control-v>", self.paste)
            self.input_box.bind("<Control-a>", self.select_all)
            self.chat_box.bind("<Control-c>", self.copy_chat_box)
            self.master.bind_class("Text", "<Control-x>", self.cut)
            self.master.bind_class("Text", "<Control-c>", self.copy)
            self.master.bind_class("Text", "<Control-v>", self.paste)
            self.master.bind_class("Text", "<Control-a>", self.select_all)

        self.context_menu = self.create_context_menu()
        self.input_box.bind("<Button-3>", self.show_context_menu)
        
        self.chat_box_context_menu = self.create_chat_box_context_menu()
        self.chat_box.bind("<Button-3>", self.show_chat_box_context_menu)

    def create_context_menu(self):
        context_menu = tk.Menu(self.input_box, tearoff=0)
        context_menu.add_command(label="Cut", command=self.cut)
        context_menu.add_command(label="Copy", command=self.copy)
        context_menu.add_command(label="Paste", command=self.paste)
        context_menu.add_command(label="Select All", command=self.select_all)
        return context_menu

    def show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)
        return "break"

    def create_chat_box_context_menu(self):
        context_menu = tk.Menu(self.chat_box, tearoff=0)
        context_menu.add_command(label="Copy", command=self.copy_chat_box)
        return context_menu

    def show_chat_box_context_menu(self, event):
        self.chat_box_context_menu.tk_popup(event.x_root, event.y_root)
        return "break"

    def cut(self, event=None):
        self.copy()
        self.input_box.delete(tk.SEL_FIRST, tk.SEL_LAST)
        return "break"

    def copy(self, event=None):
        try:
            self.master.clipboard_clear()
            selected_text = self.input_box.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.master.clipboard_append(selected_text)
        except tk.TclError:
            pass
        return "break"

    def paste(self, event=None):
        try:
            self.input_box.insert(tk.INSERT, self.master.clipboard_get())
        except tk.TclError:
            pass
        return "break"

    def select_all(self, event=None):
        self.input_box.tag_add(tk.SEL, "1.0", tk.END)
        return "break"

    def copy_chat_box(self, event=None):
        try:
            self.master.clipboard_clear()
            selected_text = self.chat_box.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.master.clipboard_append(selected_text)
        except tk.TclError:
            pass
        return "break"

    def toggle_theme(self):
        new_theme = 'light' if self.config['theme'] == 'dark' else 'dark'
        self.config['theme'] = new_theme
        self.apply_theme(new_theme)

    def save_chat(self):
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".txt")
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.chat_box.get("1.0", tk.END))
            messagebox.showinfo("Info", "대화 내용이 성공적으로 저장되었습니다.")
        except IOError as e:
            messagebox.showerror("Error", f"파일 저장 중 오류가 발생했습니다: {e}")

    def change_session(self, event=None):
        selected_index = self.session_combo.current()
        self.chat_app.change_session(selected_index)  # ChatApp의 메소드 호출
        self.update_chat_display()
        self.update_window_title()

    def new_session(self):
        new_session_name = simpledialog.askstring("New Session", "Enter a name for the new session:")
        if new_session_name:
            self.session_manager.new_session(new_session_name)
            self.session_combo['values'] = [s.name for s in self.session_manager.sessions]
            self.session_combo.set(new_session_name)
            self.change_session()

    def rename_session(self):
        current_name = self.session_manager.sessions[self.session_manager.current_session].name
        new_name = simpledialog.askstring("Rename Session", "Enter a new name for the session:", initialvalue=current_name)
        if new_name:
            self.session_manager.rename_session(new_name)
            self.session_combo['values'] = [s.name for s in self.session_manager.sessions]
            self.session_combo.set(new_name)
            self.update_window_title()

    def delete_session(self):
        self.session_manager.delete_session()
        self.session_combo['values'] = [s.name for s in self.session_manager.sessions]
        self.session_combo.set(self.session_manager.sessions[self.session_manager.current_session].name)
        self.change_session()

    def send_message(self, event=None):
        if self.chat_app:
            return self.chat_app.send_message(event)
        return "break"

    def insert_newline(self, event):
        self.input_box.insert(tk.INSERT, "\n")
        return "break"

    def attach_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if file_path and file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            self.attached_file = file_path
            file_name = os.path.basename(file_path)
            self.chat_box.config(state=tk.NORMAL)
            self.chat_box.insert(tk.END, f"File attached: {file_name}\n\n")
            self.chat_box.config(state=tk.DISABLED)
            self.chat_box.see(tk.END)
        else:
            messagebox.showerror("Error", "올바른 파일 형식이 아닙니다.")

    def update_chat_display(self):
        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.delete("1.0", tk.END)
        for message in self.session_manager.sessions[self.session_manager.current_session].messages:
            role = self.config['user_name'] if message["role"] == "user" else "Claude"
            content = message['content']
            
            if isinstance(content, list):
                for item in content:
                    if item['type'] == 'text':
                        self.chat_box.insert(tk.END, f"{role}: {item['text']}\n\n")
                    elif item['type'] == 'image':
                        self.chat_box.insert(tk.END, f"{role}: [Image attached]\n\n")
            else:
                lines = content.split('\n')
                i = 0
                while i < len(lines):
                    if lines[i].startswith('```'):
                        language = lines[i][3:].strip()
                        code_lines = []
                        i += 1
                        while i < len(lines) and not lines[i].startswith('```'):
                            code_lines.append(lines[i])
                            i += 1
                        code = '\n'.join(code_lines)
                        code_block = CodeBlock(self.chat_box, code, language)
                        self.chat_box.window_create(tk.END, window=code_block)
                        self.chat_box.insert(tk.END, '\n\n')
                    else:
                        self.chat_box.insert(tk.END, f"{role}: {lines[i]}\n")
                    i += 1
                self.chat_box.insert(tk.END, '\n')
        
        self.chat_box.config(state=tk.DISABLED)
        self.chat_box.see(tk.END)

class ChatApp:
    def __init__(self, master):
        self.master = master
        self.config = ConfigManager.load_config()
        self.session_manager = SessionManager()
        self.current_session = 0  # 여기에 current_session 초기화
        self.ui_manager = UIManager(master, self.config, self.session_manager)
        self.ui_manager.chat_app = self
        
        try:
            self.api_key = APIKeyManager.get_api_key()
            self.client = anthropic.Client(api_key=self.api_key)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            self.master.destroy()
            return

    # 세션 변경 메소드 추가
    def change_session(self, index):
        self.current_session = index

    def send_message(self, event=None):
        if event and event.state & 0x1:  # Shift key is pressed
            return self.ui_manager.insert_newline(event)
        message = self.ui_manager.input_box.get("1.0", tk.END).strip()
        if message or self.ui_manager.attached_file:
            self.ui_manager.chat_box.config(state=tk.NORMAL)
            self.ui_manager.chat_box.insert(tk.END, f"{self.config['user_name']}: {message}\n")
            if self.ui_manager.attached_file:
                file_name = os.path.basename(self.ui_manager.attached_file)
                self.ui_manager.chat_box.insert(tk.END, f"Attached file: {file_name}\n")
            self.ui_manager.chat_box.insert(tk.END, "\n")
            self.ui_manager.input_box.delete("1.0", tk.END)
            
            self.session_manager.sessions[self.session_manager.current_session].add_message("user", message)
            
            if self.ui_manager.attached_file:
                response = self.chat_with_claude_image(message, self.ui_manager.attached_file)
                self.ui_manager.attached_file = None  # Reset attached file
            else:
                response = self.chat_with_claude(message)
            
            if response:
                self.session_manager.sessions[self.session_manager.current_session].add_message("assistant", response)
                self.ui_manager.chat_box.insert(tk.END, "Claude: ")
                self.gradual_display(response)
                self.ui_manager.chat_box.insert(tk.END, "\n\n")
                self.ui_manager.chat_box.config(state=tk.DISABLED)
                self.ui_manager.chat_box.see(tk.END)
        return "break"

    def gradual_display(self, text):
        for char in text:
            self.ui_manager.chat_box.insert(tk.END, char)
            self.ui_manager.chat_box.see(tk.END)
            self.ui_manager.chat_box.update_idletasks()
            self.master.after(3)  # 3ms delay

    def chat_with_claude(self, message):
        try:
            # 기존 메시지 필터링 및 역할 교대 확인
            filtered_messages = []
            last_role = None
            for msg in self.session_manager.sessions[self.current_session].messages:
                if msg['content'].strip():  # 빈 메시지 제외
                    if msg['role'] != last_role:
                        filtered_messages.append(msg)
                        last_role = msg['role']
                    elif msg['role'] == 'user':
                        # 연속된 user 메시지의 경우, 내용을 합칩니다
                        filtered_messages[-1]['content'] += f"\n\n{msg['content']}"
            
            # 마지막 메시지가 assistant이고 비어 있다면 제거
            if filtered_messages and filtered_messages[-1]['role'] == 'assistant' and not filtered_messages[-1]['content'].strip():
                filtered_messages.pop()
            
            # 새 사용자 메시지 추가
            if filtered_messages and filtered_messages[-1]['role'] == 'user':
                filtered_messages[-1]['content'] += f"\n\n{message}"
            else:
                filtered_messages.append({'role': 'user', 'content': message})

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4000,
                messages=filtered_messages,
                temperature=0,
                system="You are a skilled Python developer tasked with reviewing and improving code. Your job is to analyze the provided Python code, identify any bugs, suggest efficiency improvements, and explain your findings concisely. Follow these steps:\n\n1. First, you will be given a Python code snippet to analyze. The code will be provided within <code> tags:\n\n<code>\n{{PYTHON_CODE}}\n</code>\n\n2. Carefully review the code and look for the following:\n a) Syntax errors\n b) Logical errors\n c) Runtime errors\n d) Inefficient algorithms or data structures\n e) Poor coding practices or style issues\n\n3. If you identify any bugs, explain each one clearly and provide a corrected version of the code snippet that fixes the bug.\n\n4. Consider ways to improve the efficiency of the code. This may include:\n a) Using more appropriate data structures\n b) Optimizing algorithms\n c) Reducing unnecessary operations\n d) Improving readability and maintainability\n\n5. Present your findings and suggestions in the following format:\n\n<analysis>\n<bugs>\n[List each bug you've found, explain it, and provide the corrected code snippet]\n</bugs>\n\n<efficiency_improvements>\n[List your suggestions for improving the efficiency of the code, explaining the benefits of each suggestion]\n</efficiency_improvements>\n\n<summary>\n[Provide a brief summary of your overall assessment of the code and the most important improvements to be made]\n</summary>\n</analysis>\n\nRemember to be thorough in your analysis but concise in your explanations. Focus on the most critical issues and improvements that will have the biggest impact on the code's functionality and efficiency."
            )
            return response.content[0].text if response.content else "응답 내용이 없습니다."
        except anthropic.APIError as e:
            error_message = f"Claude API 오류: {str(e)}"
            messagebox.showerror("API Error", error_message)
            return error_message
        except Exception as e:
            error_message = f"예상치 못한 오류 발생: {str(e)}"
            messagebox.showerror("Error", error_message)
            return error_message

    def chat_with_claude_image(self, message, image_path):
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        messages = [{'role': msg['role'], 'content': msg['content']} 
                    for msg in self.session_manager.sessions[self.session_manager.current_session].messages 
                    if msg['content'].strip()]
        messages.append({
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': message
                },
                {
                    'type': 'image',
                    'image_url': {
                        'url': f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        })

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4000,
                messages=messages
            )
            return response.content[0].text if response.content else "No response content"
        except Exception as e:
            print(f"Error: {e}")
            return "Error: Unable to get a response from Claude."

    def on_closing(self):
        self.config['window_size'] = f"{self.master.winfo_width()}x{self.master.winfo_height()}"
        ConfigManager.save_config(self.config)
        self.session_manager.save_sessions()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()