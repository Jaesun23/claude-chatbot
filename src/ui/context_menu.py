import tkinter as tk
from typing import Callable, Dict, Any
from dataclasses import dataclass
from events import EventEmitter, Event, UIEventType

@dataclass
class MenuAction:
    """메뉴 액션 정의"""
    label: str
    command: Callable
    accelerator: str = None
    condition: Callable = None

class ContextMenuManager:
    """컨텍스트 메뉴 관리 클래스"""
    
    def __init__(self, event_emitter: EventEmitter):
        self.event_emitter = event_emitter
        self.menus: Dict[str, tk.Menu] = {}
        
    def create_chat_menu(self, parent: tk.Widget) -> tk.Menu:
        """채팅 영역 컨텍스트 메뉴 생성"""
        menu = tk.Menu(parent, tearoff=0)
        
        menu.add_command(
            label="Copy",
            accelerator="Ctrl+C",
            command=lambda: self._copy_selection(parent)
        )
        menu.add_separator()
        menu.add_command(
            label="Clear All",
            command=lambda: self._clear_chat(parent)
        )
        
        self.menus['chat'] = menu
        return menu
        
    def create_input_menu(self, parent: tk.Widget) -> tk.Menu:
        """입력 영역 컨텍스트 메뉴 생성"""
        menu = tk.Menu(parent, tearoff=0)
        
        menu.add_command(
            label="Cut",
            accelerator="Ctrl+X",
            command=lambda: self._cut_selection(parent)
        )
        menu.add_command(
            label="Copy",
            accelerator="Ctrl+C",
            command=lambda: self._copy_selection(parent)
        )
        menu.add_command(
            label="Paste",
            accelerator="Ctrl+V",
            command=lambda: self._paste_selection(parent)
        )
        menu.add_separator()
        menu.add_command(
            label="Select All",
            accelerator="Ctrl+A",
            command=lambda: self._select_all(parent)
        )
        
        self.menus['input'] = menu
        return menu
        
    def show_menu(self, menu_name: str, event):
        """컨텍스트 메뉴 표시"""
        menu = self.menus.get(menu_name)
        if menu:
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
                
    def _copy_selection(self, widget: tk.Widget):
        """선택 영역 복사"""
        try:
            selection = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            widget.clipboard_clear()
            widget.clipboard_append(selection)
            self.event_emitter.emit(Event(
                UIEventType.STATE_CHANGE.value,
                {"action": "copy", "success": True}
            ))
        except tk.TclError:
            pass
            
    def _cut_selection(self, widget: tk.Widget):
        """선택 영역 잘라내기"""
        if not isinstance(widget, tk.Text):
            return
            
        try:
            selection = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            widget.clipboard_clear()
            widget.clipboard_append(selection)
            widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.event_emitter.emit(Event(
                UIEventType.STATE_CHANGE.value,
                {"action": "cut", "success": True}
            ))
        except tk.TclError:
            pass
            
    def _paste_selection(self, widget: tk.Widget):
        """클립보드 내용 붙여넣기"""
        if not isinstance(widget, tk.Text):
            return
            
        try:
            text = widget.selection_get(selection="CLIPBOARD")
            widget.insert(tk.INSERT, text)
            self.event_emitter.emit(Event(
                UIEventType.STATE_CHANGE.value,
                {"action": "paste", "success": True}
            ))
        except tk.TclError:
            pass
            
    def _select_all(self, widget: tk.Widget):
        """전체 선택"""
        if not isinstance(widget, tk.Text):
            return
            
        widget.tag_add(tk.SEL, "1.0", tk.END)
        widget.mark_set(tk.INSERT, "1.0")
        widget.see(tk.INSERT)
            
    def _clear_chat(self, widget: tk.Widget):
        """채팅 내용 전체 삭제"""
        if not isinstance(widget, tk.Text):
            return
            
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.config(state=tk.DISABLED)
        
        self.event_emitter.emit(Event(
            UIEventType.STATE_CHANGE.value,
            {"action": "clear_chat", "success": True}
        ))