# file: CLAI/gui/app.py
# CLAI GUI - Modern directory browser with AI-powered command execution

import os
import sys
import json
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


# ============================================================
# MODERN THEME
# ============================================================
class Theme:
    # Backgrounds
    BG = "#f0f0f5"
    CARD = "#ffffff"
    CARD_HOVER = "#fafafa"
    
    # Accents
    BLUE = "#007aff"
    BLUE_LIGHT = "#e8f4fd"
    BLUE_DARK = "#0056b3"
    GREEN = "#34c759"
    GREEN_LIGHT = "#e8f9ed"
    GREEN_DARK = "#2da44e"
    
    # Status
    SUCCESS = "#34c759"
    WARNING = "#ff9f0a"
    ERROR = "#ff3b30"
    
    # Text
    TEXT = "#1c1c1e"
    TEXT_SEC = "#8e8e93"
    TEXT_LIGHT = "#aeaeb2"
    
    # Terminal
    TERM_BG = "#1c1c1e"
    TERM_FG = "#f5f5f7"
    
    # Fonts
    FONT = ("Segoe UI", 10)
    FONT_BOLD = ("Segoe UI", 10, "bold")
    FONT_TITLE = ("Segoe UI", 12, "bold")
    FONT_MONO = ("Consolas", 10)
    FONT_SMALL = ("Segoe UI", 9)


class RoundedFrame(tk.Canvas):
    """A frame with rounded corners"""
    def __init__(self, parent, bg=Theme.CARD, radius=12, **kwargs):
        super().__init__(parent, bg=Theme.BG, highlightthickness=0, **kwargs)
        self.radius = radius
        self.bg_color = bg
        self.bind("<Configure>", self._draw)
        
    def _draw(self, event=None):
        self.delete("bg")
        w, h, r = self.winfo_width(), self.winfo_height(), self.radius
        self.create_rounded_rect(0, 0, w, h, r, fill=self.bg_color, tags="bg")
        self.tag_lower("bg")
    
    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
            x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
            x1, y2, x1, y2-r, x1, y1+r, x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)


class RoundedButton(tk.Canvas):
    """Rounded button with smooth edges"""
    def __init__(self, parent, text="", command=None, 
                 bg=Theme.BLUE, fg="white", width=None, height=36, radius=10, **kwargs):
        super().__init__(parent, height=height,
                        bg=parent.cget("bg") if hasattr(parent, 'cget') else Theme.BG,
                        highlightthickness=0, **kwargs)
        
        self.bg_color = bg
        self.fg_color = fg
        self.text = text
        self.command = command
        self.radius = radius
        self.hover = False
        self.width = width
        self._enabled = True
        
        # Calculate width from text if not provided
        if width is None:
            temp_label = tk.Label(parent, text=text, font=Theme.FONT_BOLD)
            temp_label.update()
            width = temp_label.winfo_reqwidth() + 32
            temp_label.destroy()
        
        self.configure(width=width)
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", self._draw)
        self._draw()
    
    def _draw(self, event=None):
        self.delete("all")
        w, h, r = self.winfo_width() or 100, self.winfo_height() or 36, self.radius
        
        # Use disabled color if not enabled
        if not self._enabled:
            color = Theme.BG
            text_color = Theme.TEXT_LIGHT
        else:
            # Darken on hover
            color = self._darken(self.bg_color, 20) if self.hover else self.bg_color
            text_color = self.fg_color
        
        # Draw rounded rectangle using arcs
        self.create_arc(0, 0, r*2, r*2, start=90, extent=90, fill=color, outline="")
        self.create_arc(w-r*2, 0, w, r*2, start=0, extent=90, fill=color, outline="")
        self.create_arc(0, h-r*2, r*2, h, start=180, extent=90, fill=color, outline="")
        self.create_arc(w-r*2, h-r*2, w, h, start=270, extent=90, fill=color, outline="")
        self.create_rectangle(r, 0, w-r, h, fill=color, outline="")
        self.create_rectangle(0, r, w, h-r, fill=color, outline="")
        
        # Draw text
        self.create_text(w//2, h//2, text=self.text, fill=text_color, font=Theme.FONT_BOLD)
    
    def _darken(self, color, amount):
        r = max(0, min(255, int(color[1:3], 16) - amount))
        g = max(0, min(255, int(color[3:5], 16) - amount))
        b = max(0, min(255, int(color[5:7], 16) - amount))
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _on_enter(self, e):
        if self._enabled:
            self.hover = True
            self.configure(cursor="hand2")
            self._draw()
    
    def _on_leave(self, e):
        self.hover = False
        self._draw()
    
    def _on_click(self, e):
        if self._enabled:
            self.hover = True
            self._draw()
    
    def _on_release(self, e):
        self.hover = False
        self._draw()
        if self._enabled and self.command:
            self.command()
    
    def configure(self, **kwargs):
        if "state" in kwargs:
            self._enabled = kwargs["state"] == "normal"
            self._draw()
        else:
            super().configure(**kwargs)


class ModernEntry(tk.Frame):
    """Modern rounded entry with colored background"""
    def __init__(self, parent, bg_color=Theme.CARD, border_color=Theme.BLUE_LIGHT,
                 placeholder="", **kwargs):
        super().__init__(parent, bg=bg_color)
        
        self.bg_color = bg_color
        self.border_color = border_color
        self.placeholder = placeholder
        self.has_placeholder = True
        
        # Outer frame for border effect
        self.outer = tk.Frame(self, bg=border_color, padx=2, pady=2)
        self.outer.pack(fill="both", expand=True)
        
        # Inner frame
        self.inner = tk.Frame(self.outer, bg=bg_color)
        self.inner.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Entry
        self.entry = tk.Entry(self.inner, 
            bg=bg_color, fg=Theme.TEXT_LIGHT,
            font=Theme.FONT, relief="flat", 
            insertbackground=Theme.TEXT,
            **kwargs
        )
        self.entry.pack(fill="both", expand=True, padx=12, pady=10)
        
        if placeholder:
            self.entry.insert(0, placeholder)
            self.entry.bind("<FocusIn>", self._on_focus_in)
            self.entry.bind("<FocusOut>", self._on_focus_out)
    
    def _on_focus_in(self, e):
        if self.has_placeholder:
            self.entry.delete(0, "end")
            self.entry.configure(fg=Theme.TEXT)
            self.has_placeholder = False
    
    def _on_focus_out(self, e):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.configure(fg=Theme.TEXT_LIGHT)
            self.has_placeholder = True
    
    def get(self):
        if self.has_placeholder:
            return ""
        return self.entry.get()
    
    def delete(self, first, last):
        self.entry.delete(first, last)
    
    def bind(self, event, callback):
        self.entry.bind(event, callback)


# ============================================================
# TERMINAL PANEL
# ============================================================
class TerminalPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=Theme.CARD)
        
        # Header
        header = tk.Frame(self, bg=Theme.CARD)
        header.pack(fill="x", padx=16, pady=(16, 8))
        
        tk.Label(header, text="Terminal", font=Theme.FONT_TITLE,
            bg=Theme.CARD, fg=Theme.TEXT).pack(side="left")
        
        clear_btn = RoundedButton(header, text="Clear",
            bg=Theme.BG, fg=Theme.BLUE, height=32, radius=8,
            command=self.clear)
        clear_btn.pack(side="right")
        
        # Terminal with rounded corners effect
        term_container = tk.Frame(self, bg=Theme.TERM_BG, padx=2, pady=2)
        term_container.pack(fill="both", expand=True, padx=16, pady=8)
        
        term_inner = tk.Frame(term_container, bg=Theme.TERM_BG)
        term_inner.pack(fill="both", expand=True)
        
        self.terminal = tk.Text(term_inner,
            bg=Theme.TERM_BG, fg=Theme.TERM_FG,
            font=Theme.FONT_MONO, wrap="word",
            relief="flat", padx=16, pady=12,
            insertbackground=Theme.TERM_FG,
            highlightthickness=0
        )
        
        scrollbar = tk.Scrollbar(term_inner, command=self.terminal.yview,
            bg=Theme.TERM_BG, troughcolor=Theme.TERM_BG)
        self.terminal.configure(yscrollcommand=scrollbar.set)
        
        self.terminal.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Tags
        self.terminal.tag_configure("cmd", foreground="#64d2ff")
        self.terminal.tag_configure("ok", foreground="#30d158")
        self.terminal.tag_configure("err", foreground="#ff453a")
        self.terminal.tag_configure("info", foreground="#ffd60a")
        self.terminal.tag_configure("ai", foreground="#bf5af2")
        self.terminal.tag_configure("time", foreground="#8e8e93")
        
        # Input with green tint
        input_frame = tk.Frame(self, bg=Theme.CARD)
        input_frame.pack(fill="x", padx=16, pady=(8, 16))
        
        # Green-tinted input container
        input_container = tk.Frame(input_frame, bg=Theme.GREEN_LIGHT, padx=2, pady=2)
        input_container.pack(fill="x")
        
        input_inner = tk.Frame(input_container, bg=Theme.GREEN_LIGHT)
        input_inner.pack(fill="x", padx=1, pady=1)
        
        prompt = tk.Label(input_inner, text="❯", 
            bg=Theme.GREEN_LIGHT, fg=Theme.GREEN,
            font=(Theme.FONT_MONO[0], 12, "bold"))
        prompt.pack(side="left", padx=(12, 6))
        
        self.cmd_entry = tk.Entry(input_inner,
            bg=Theme.GREEN_LIGHT, fg=Theme.TEXT,
            font=Theme.FONT_MONO, relief="flat",
            insertbackground=Theme.GREEN
        )
        self.cmd_entry.pack(side="left", fill="x", expand=True, pady=10)
        self.cmd_entry.bind("<Return>", self._on_cmd)
        
        run_btn = RoundedButton(input_inner, text="Run",
            bg=Theme.GREEN, fg="white", height=36, radius=8,
            command=self._on_cmd)
        run_btn.pack(side="right", padx=8, pady=6)
        
        self.callback: Optional[Callable] = None
        self.terminal.configure(state="disabled")
    
    def log(self, msg: str, tag: str = None):
        self.terminal.configure(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self.terminal.insert("end", f"[{ts}] ", "time")
        self.terminal.insert("end", msg + "\n", tag)
        self.terminal.see("end")
        self.terminal.configure(state="disabled")
    
    def log_cmd(self, cmd: str):
        self.log(f"$ {cmd}", "cmd")
    
    def log_out(self, out: str, err: bool = False):
        for line in out.strip().split("\n"):
            if line:
                self.log(line, "err" if err else "ok")
    
    def log_ai(self, msg: str):
        self.log(f"🤖 {msg}", "ai")
    
    def clear(self):
        self.terminal.configure(state="normal")
        self.terminal.delete("1.0", "end")
        self.terminal.configure(state="disabled")
    
    def _on_cmd(self, e=None):
        cmd = self.cmd_entry.get().strip()
        if cmd and self.callback:
            self.cmd_entry.delete(0, "end")
            self.callback(cmd)


# ============================================================
# AI COMMAND BAR
# ============================================================
class AICommandBar(tk.Frame):
    def __init__(self, parent, on_submit: Callable):
        super().__init__(parent, bg=Theme.CARD)
        self.on_submit = on_submit
        
        container = tk.Frame(self, bg=Theme.CARD)
        container.pack(fill="x", padx=16, pady=16)
        
        # Header
        header = tk.Frame(container, bg=Theme.CARD)
        header.pack(fill="x", pady=(0, 10))
        
        tk.Label(header, text="🤖 AI Assistant", font=Theme.FONT_TITLE,
            bg=Theme.CARD, fg=Theme.TEXT).pack(side="left")
        
        self.status = tk.Label(header, text="", font=Theme.FONT_SMALL,
            bg=Theme.CARD, fg=Theme.TEXT_SEC)
        self.status.pack(side="right")
        
        # Blue-tinted input
        input_frame = tk.Frame(container, bg=Theme.BLUE_LIGHT, padx=2, pady=2)
        input_frame.pack(fill="x")
        
        input_inner = tk.Frame(input_frame, bg=Theme.BLUE_LIGHT)
        input_inner.pack(fill="x", padx=1, pady=1)
        
        self.entry = tk.Entry(input_inner,
            bg=Theme.BLUE_LIGHT, fg=Theme.TEXT,
            font=Theme.FONT, relief="flat",
            insertbackground=Theme.BLUE
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=14, pady=12)
        self.entry.insert(0, "Describe what you want to do...")
        self.entry.configure(fg=Theme.TEXT_LIGHT)
        self.entry.bind("<Return>", self._submit)
        self.entry.bind("<FocusIn>", self._focus_in)
        self.entry.bind("<FocusOut>", self._focus_out)
        self.placeholder = True
        
        self.btn = RoundedButton(input_inner, text="Execute",
            bg=Theme.BLUE, fg="white", height=36, radius=8,
            command=self._submit)
        self.btn.pack(side="right", padx=8, pady=6)
    
    def _focus_in(self, e):
        if self.placeholder:
            self.entry.delete(0, "end")
            self.entry.configure(fg=Theme.TEXT)
            self.placeholder = False
    
    def _focus_out(self, e):
        if not self.entry.get():
            self.entry.insert(0, "Describe what you want to do...")
            self.entry.configure(fg=Theme.TEXT_LIGHT)
            self.placeholder = True
    
    def _submit(self, e=None):
        q = self.entry.get().strip()
        if q and not self.placeholder:
            self.entry.delete(0, "end")
            self.on_submit(q)
    
    def set_status(self, text: str):
        self.status.configure(text=text)
    
    def set_enabled(self, enabled: bool):
        self.entry.configure(state="normal" if enabled else "disabled")


# ============================================================
# DIRECTORY BROWSER
# ============================================================
class DirectoryBrowser(tk.Frame):
    def __init__(self, parent, on_select: Callable = None):
        super().__init__(parent, bg=Theme.CARD)
        self.on_select = on_select
        self.current_path: Optional[Path] = None
        
        # Header
        header = tk.Frame(self, bg=Theme.CARD)
        header.pack(fill="x", padx=16, pady=16)
        
        # Open button - rounded
        open_btn = RoundedButton(header, text="📁 Open Folder",
            bg=Theme.BLUE, fg="white", height=38, radius=10,
            command=self.browse)
        open_btn.pack(side="left")
        
        # Refresh button - rounded
        ref_btn = RoundedButton(header, text="↻",
            bg=Theme.BG, fg=Theme.TEXT, width=40, height=38, radius=10,
            command=self.refresh)
        ref_btn.pack(side="left", padx=(8, 0))
        
        # Path
        path_frame = tk.Frame(self, bg=Theme.CARD)
        path_frame.pack(fill="x", padx=16)
        
        self.path_var = tk.StringVar(value="No folder selected")
        tk.Label(path_frame, textvariable=self.path_var, font=Theme.FONT_SMALL,
            bg=Theme.CARD, fg=Theme.TEXT_SEC).pack(anchor="w")
        
        # Tree
        tree_frame = tk.Frame(self, bg=Theme.CARD)
        tree_frame.pack(fill="both", expand=True, padx=16, pady=(8, 16))
        
        style = ttk.Style()
        style.configure("Browser.Treeview",
            background=Theme.CARD, foreground=Theme.TEXT,
            fieldbackground=Theme.CARD, rowheight=32,
            font=Theme.FONT)
        style.configure("Browser.Treeview.Heading",
            background=Theme.BG, foreground=Theme.TEXT_SEC,
            font=Theme.FONT_SMALL)
        style.map("Browser.Treeview",
            background=[("selected", Theme.BLUE_LIGHT)],
            foreground=[("selected", Theme.BLUE)])
        
        self.tree = ttk.Treeview(tree_frame, columns=("size", "mod"),
            selectmode="browse", style="Browser.Treeview")
        self.tree.heading("#0", text="Name", anchor="w")
        self.tree.heading("size", text="Size", anchor="e")
        self.tree.heading("mod", text="Modified", anchor="w")
        self.tree.column("#0", width=200, minwidth=150)
        self.tree.column("size", width=60, minwidth=50, anchor="e")
        self.tree.column("mod", width=90, minwidth=80)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        self.tree.bind("<Double-1>", self._dbl_click)
        self.tree.bind("<Button-3>", self._right_click)
        
        # Context menu
        self.menu = tk.Menu(self, tearoff=0, bg=Theme.CARD, fg=Theme.TEXT,
            activebackground=Theme.BLUE_LIGHT, activeforeground=Theme.BLUE,
            font=Theme.FONT)
        self.menu.add_command(label="   📂 Open", command=self._ctx_open)
        self.menu.add_command(label="   🗑️ Delete", command=self._ctx_delete)
        self.menu.add_command(label="   📋 Copy Path", command=self._ctx_copy)
        
        self.on_file_action: Optional[Callable] = None
    
    def browse(self):
        path = filedialog.askdirectory(title="Select Folder")
        if path:
            self.set_path(path)
    
    def set_path(self, path: str):
        self.current_path = Path(path)
        self.path_var.set(str(self.current_path))
        self.refresh()
        if self.on_select:
            self.on_select(self.current_path)
    
    def refresh(self):
        if not self.current_path or not self.current_path.exists():
            return
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if self.current_path.parent != self.current_path:
            self.tree.insert("", "end", text="📁  ..", values=("", ""))
        
        try:
            items = sorted(self.current_path.iterdir(),
                key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                if item.name.startswith("."):
                    continue
                try:
                    if item.is_dir():
                        self.tree.insert("", "end", text=f"📁  {item.name}", values=("", ""))
                    else:
                        icon = self._icon(item.suffix)
                        size = self._size(item.stat().st_size)
                        mod = datetime.fromtimestamp(item.stat().st_mtime).strftime("%m/%d %H:%M")
                        self.tree.insert("", "end", text=f"{icon}  {item.name}", values=(size, mod))
                except:
                    pass
        except Exception as e:
            print(f"Error: {e}")
    
    def _icon(self, ext: str) -> str:
        icons = {".py": "🐍", ".js": "📜", ".html": "🌐", ".css": "🎨",
            ".json": "📋", ".txt": "📄", ".md": "📝", ".log": "📃",
            ".jpg": "🖼️", ".png": "🖼️", ".zip": "📦", ".exe": "⚙️"}
        return icons.get(ext.lower(), "📄")
    
    def _size(self, s: int) -> str:
        for u in ["B", "K", "M", "G"]:
            if s < 1024:
                return f"{s:.0f}{u}"
            s /= 1024
        return f"{s:.0f}T"
    
    def _get_path(self) -> Optional[Path]:
        sel = self.tree.selection()
        if not sel or not self.current_path:
            return None
        text = self.tree.item(sel[0])["text"]
        name = text.split("  ", 1)[-1]
        if name == "..":
            return self.current_path.parent
        return self.current_path / name
    
    def _dbl_click(self, e):
        path = self._get_path()
        if path:
            if path.is_dir():
                self.set_path(str(path))
            else:
                try:
                    os.startfile(str(path))
                except:
                    pass
    
    def _right_click(self, e):
        item = self.tree.identify_row(e.y)
        if item:
            self.tree.selection_set(item)
            self.menu.post(e.x_root, e.y_root)
    
    def _ctx_open(self):
        path = self._get_path()
        if path:
            if path.is_dir():
                self.set_path(str(path))
            else:
                try:
                    os.startfile(str(path))
                except:
                    pass
    
    def _ctx_delete(self):
        path = self._get_path()
        if path and path.name != "..":
            if messagebox.askyesno("Delete", f"Delete '{path.name}'?"):
                try:
                    if path.is_dir():
                        import shutil
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    self.refresh()
                    if self.on_file_action:
                        self.on_file_action("delete", path)
                except Exception as e:
                    messagebox.showerror("Error", str(e))
    
    def _ctx_copy(self):
        path = self._get_path()
        if path:
            self.clipboard_clear()
            self.clipboard_append(str(path))


# ============================================================
# SANDBOX CONTROL BAR
# ============================================================
class SandboxBar(tk.Frame):
    def __init__(self, parent, on_apply, on_discard, on_show):
        super().__init__(parent, bg=Theme.CARD)
        
        container = tk.Frame(self, bg=Theme.CARD)
        container.pack(fill="x", padx=16, pady=16)
        
        # Left - status
        left = tk.Frame(container, bg=Theme.CARD)
        left.pack(side="left")
        
        self.icon = tk.Label(left, text="⚪", font=("Segoe UI", 16), bg=Theme.CARD)
        self.icon.pack(side="left")
        
        text_frame = tk.Frame(left, bg=Theme.CARD)
        text_frame.pack(side="left", padx=(8, 0))
        
        self.title = tk.Label(text_frame, text="Sandbox", font=Theme.FONT_BOLD,
            bg=Theme.CARD, fg=Theme.TEXT)
        self.title.pack(anchor="w")
        
        self.detail = tk.Label(text_frame, text="Open a folder to start",
            font=Theme.FONT_SMALL, bg=Theme.CARD, fg=Theme.TEXT_SEC)
        self.detail.pack(anchor="w")
        
        # Right - buttons
        right = tk.Frame(container, bg=Theme.CARD)
        right.pack(side="right")
        
        # Show changes button - rounded
        self.btn_show = RoundedButton(right, text="📋 Changes",
            bg=Theme.BG, fg=Theme.TEXT, height=36, radius=8,
            command=on_show)
        self.btn_show.pack(side="left", padx=2)
        
        # Discard button - rounded
        self.btn_discard = RoundedButton(right, text="🗑️ Discard",
            bg=Theme.BG, fg=Theme.TEXT, height=36, radius=8,
            command=on_discard)
        self.btn_discard.pack(side="left", padx=2)
        
        # Apply button - rounded
        self.btn_apply = RoundedButton(right, text="✓ Apply",
            bg=Theme.SUCCESS, fg="white", height=36, radius=8,
            command=on_apply)
        self.btn_apply.pack(side="left", padx=(2, 0))
    
    def update(self, active: bool, changes: int, detail: str = ""):
        if active:
            if changes > 0:
                self.icon.configure(text="🟡")
                self.title.configure(text=f"Sandbox • {changes} changes")
                # Update apply button to green
                self.btn_apply.bg_color = Theme.SUCCESS
                self.btn_apply.fg_color = "white"
                self.btn_apply._draw()
            else:
                self.icon.configure(text="🟢")
                self.title.configure(text="Sandbox Active")
                # Update apply button to gray
                self.btn_apply.bg_color = Theme.BG
                self.btn_apply.fg_color = Theme.TEXT_SEC
                self.btn_apply._draw()
            self.detail.configure(text=detail if detail else "Ready")
            self.btn_show.configure(state="normal")
            self.btn_discard.configure(state="normal")
        else:
            self.icon.configure(text="⚪")
            self.title.configure(text="No Sandbox")
            self.detail.configure(text="Open a folder")
            self.btn_apply.bg_color = Theme.BG
            self.btn_apply.fg_color = Theme.TEXT_SEC
            self.btn_apply._draw()
            self.btn_show.configure(state="disabled")
            self.btn_discard.configure(state="disabled")


# ============================================================
# MAIN APP
# ============================================================
class CLAIApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CLAI")
        self.root.geometry("1150x800")
        self.root.minsize(950, 650)
        self.root.configure(bg=Theme.BG)
        
        # Main container
        main = tk.Frame(self.root, bg=Theme.BG)
        main.pack(fill="both", expand=True, padx=12, pady=12)
        
        # Left card - Browser
        left = tk.Frame(main, bg=Theme.CARD)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        
        tk.Label(left, text="📁 Files", font=Theme.FONT_TITLE,
            bg=Theme.CARD, fg=Theme.TEXT).pack(anchor="w", padx=16, pady=(16, 0))
        
        self.browser = DirectoryBrowser(left, on_select=self._on_dir)
        self.browser.pack(fill="both", expand=True)
        self.browser.on_file_action = self._on_file
        
        # Right card
        right = tk.Frame(main, bg=Theme.CARD)
        right.pack(side="right", fill="both", expand=True, padx=(6, 0))
        
        # AI bar
        self.ai_bar = AICommandBar(right, on_submit=self._on_ai)
        self.ai_bar.pack(fill="x")
        
        # Separator
        tk.Frame(right, bg=Theme.BG, height=1).pack(fill="x", padx=16)
        
        # Sandbox bar
        self.sandbox = SandboxBar(right, self._apply, self._discard, self._show)
        self.sandbox.pack(fill="x")
        
        # Separator
        tk.Frame(right, bg=Theme.BG, height=1).pack(fill="x", padx=16)
        
        # Terminal
        self.terminal = TerminalPanel(right)
        self.terminal.pack(fill="both", expand=True)
        self.terminal.callback = self._on_cmd
        
        # Status
        status = tk.Frame(self.root, bg=Theme.BG, height=32)
        status.pack(fill="x", side="bottom")
        status.pack_propagate(False)
        
        self.status_var = tk.StringVar(value="Ready • Open a folder to begin")
        tk.Label(status, textvariable=self.status_var,
            bg=Theme.BG, fg=Theme.TEXT_SEC, font=Theme.FONT_SMALL,
            anchor="w", padx=16).pack(fill="both", expand=True)
        
        # State
        self.current_dir = None
        self.session = None
        
        self.terminal.log("Welcome to CLAI", "info")
    
    def _on_dir(self, path: Path):
        self.current_dir = path
        self.status_var.set(f"📁 {path.name}")
        self.terminal.log(f"Opened: {path}", "info")
        
        from CLAI.sandbox.session import SandboxSession
        if self.session and self.session.is_active():
            self.session.discard()
        
        self.session = SandboxSession(work_dir=str(path))
        self.session.start()
        
        sb_path = self.session.get_sandbox_path()
        self.browser.current_path = sb_path
        self.browser.path_var.set(f"📦 {sb_path.name}")
        self.browser.refresh()
        
        self.terminal.log("Sandbox ready", "ok")
        self._update()
    
    def _update(self):
        if self.session and self.session.is_active():
            try:
                changes = self.session.get_changes()
                n = len(changes) if changes else 0
                detail = ", ".join([c.path.split("/")[-1] for c in changes[:2]])
                if n > 2:
                    detail += f" +{n-2}"
                self.sandbox.update(True, n, detail)
            except Exception as e:
                self.sandbox.update(True, 0, str(e))
        else:
            self.sandbox.update(False, 0)
    
    def _apply(self):
        if not self.session:
            return
        changes = self.session.get_changes()
        if not changes:
            self.terminal.log("No changes", "info")
            return
        
        if messagebox.askyesno("Apply", f"Apply {len(changes)} changes?"):
            self.session.apply_changes()
            self.terminal.log(f"✓ Applied {len(changes)} changes", "ok")
            
            from CLAI.sandbox.session import SandboxSession
            self.session = SandboxSession(work_dir=str(self.current_dir))
            self.session.start()
            sb = self.session.get_sandbox_path()
            self.browser.current_path = sb
            self.browser.path_var.set(f"📦 {sb.name}")
            self.browser.refresh()
        self._update()
    
    def _discard(self):
        if not self.session:
            return
        changes = self.session.get_changes()
        if changes and not messagebox.askyesno("Discard", f"Discard {len(changes)} changes?"):
            return
        
        self.session.discard()
        self.terminal.log("Sandbox reset", "info")
        
        from CLAI.sandbox.session import SandboxSession
        self.session = SandboxSession(work_dir=str(self.current_dir))
        self.session.start()
        sb = self.session.get_sandbox_path()
        self.browser.current_path = sb
        self.browser.path_var.set(f"📦 {sb.name}")
        self.browser.refresh()
        self._update()
    
    def _show(self):
        if not self.session:
            return
        self.terminal.log(self.session.show_changes(), "info")
    
    def _on_file(self, action, path, *args):
        self.terminal.log(f"{action}: {path.name}", "cmd")
        self._update()
    
    def _get_plan(self, q: str):
        try:
            from CLAI.llm.adapter_hf import HFClient
            from CLAI.llm.config_hf import get_hf_config
            from CLAI.prompt_builder.base_prompts import SYSTEM_PROMPT
            
            shots = [
                {"role": "user", "content": "list files"},
                {"role": "assistant", "content": '{"version":"1.0","intent":"list","command":["cmd","/c","dir"],"cwd":".","inputs":[],"outputs":[],"explain":"List files"}'},
            ]
            
            cfg = get_hf_config()
            client = HFClient(base=cfg["base"], token=cfg["token"], model=cfg["model"])
            
            resp = client.chat_completions([
                {"role": "system", "content": f"{SYSTEM_PROMPT}\nUse Windows cmd /c commands. Return only JSON."},
                *shots, {"role": "user", "content": q}
            ], max_tokens=500, temperature=0.1)
            
            content = resp["choices"][0]["message"]["content"].strip()
            for p in ["```json", "```"]:
                if content.startswith(p):
                    content = content[len(p):]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content.strip())
        except Exception as e:
            self.terminal.log(f"LLM Error: {e}", "err")
            return None
    
    def _on_ai(self, q: str):
        if not self.current_dir:
            messagebox.showwarning("Error", "Open a folder first")
            return
        
        self.terminal.log_ai(f"Query: {q}")
        self.ai_bar.set_status("⏳ Thinking...")
        self.ai_bar.set_enabled(False)
        
        def thread():
            plan = self._get_plan(q)
            self.root.after(0, lambda: self._handle(plan, user_query=q))
        
        threading.Thread(target=thread, daemon=True).start()
    
    def _handle(self, plan, user_query: Optional[str] = None):
        self.ai_bar.set_enabled(True)
        self.ai_bar.set_status("")
        
        if not plan:
            return
        
        cmd = " ".join(plan.get("command", []))
        self.terminal.log_ai(f"→ {plan.get('explain', cmd)}")
        
        if messagebox.askyesno("Execute?", f"Run: {cmd}"):
            self._exec(plan, user_query=user_query)
    
    def _exec(self, plan, user_query: Optional[str] = None):
        if not self.session:
            return
        
        self.terminal.log_cmd(" ".join(plan.get("command", [])))
        
        try:
            result = self.session.run_plan(plan, user_query=user_query)
            if result.stdout:
                self.terminal.log_out(result.stdout)
            if result.stderr:
                self.terminal.log_out(result.stderr, True)
            self.terminal.log(f"{'✓' if result.success else '✗'} Exit: {result.exit_code}",
                "ok" if result.success else "err")
            self.browser.refresh()
            self._update()
        except Exception as e:
            self.terminal.log(f"Error: {e}", "err")
    
    def _on_cmd(self, cmd: str):
        if not self.session:
            self.terminal.log("Open a folder first", "err")
            return
        
        sb = self.session.get_sandbox_path()
        self.terminal.log_cmd(cmd)
        
        import time
        start_time = time.time()
        
        try:
            result = subprocess.run(
                f'cmd /c {cmd}' if os.name == 'nt' else cmd,
                shell=True, cwd=str(sb),
                capture_output=True, text=True, timeout=30
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the command execution
            if hasattr(self.session, 'logger'):
                plan_dict = {
                    "version": "1.0",
                    "intent": "terminal_command",
                    "command": [cmd],
                    "cwd": ".",
                }
                self.session.logger.log_command(
                    user_query=f"Terminal command: {cmd}",
                    plan=plan_dict,
                    exit_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    duration_ms=duration_ms,
                    sandbox_mode="sandbox",
                    approved=True,
                    error=result.stderr if result.returncode != 0 else None
                )
            
            if result.stdout:
                self.terminal.log_out(result.stdout)
            if result.stderr:
                self.terminal.log_out(result.stderr, True)
            self.terminal.log(f"{'✓' if result.returncode == 0 else '✗'} Exit: {result.returncode}",
                "ok" if result.returncode == 0 else "err")
            
            self.browser.refresh()
            self._update()
        except subprocess.TimeoutExpired:
            self.terminal.log("Timeout", "err")
            if hasattr(self.session, 'logger'):
                plan_dict = {
                    "version": "1.0",
                    "intent": "terminal_command",
                    "command": [cmd],
                    "cwd": ".",
                }
                self.session.logger.log_command(
                    user_query=f"Terminal command: {cmd}",
                    plan=plan_dict,
                    exit_code=-1,
                    stdout="",
                    stderr="Command timed out after 30s",
                    duration_ms=(time.time() - start_time) * 1000,
                    sandbox_mode="sandbox",
                    approved=True,
                    error="Timeout"
                )
        except Exception as e:
            self.terminal.log(f"Error: {e}", "err")
            if hasattr(self.session, 'logger'):
                plan_dict = {
                    "version": "1.0",
                    "intent": "terminal_command",
                    "command": [cmd],
                    "cwd": ".",
                }
                self.session.logger.log_command(
                    user_query=f"Terminal command: {cmd}",
                    plan=plan_dict,
                    exit_code=-1,
                    stdout="",
                    stderr=str(e),
                    duration_ms=(time.time() - start_time) * 1000,
                    sandbox_mode="sandbox",
                    approved=True,
                    error=str(e)
                )
    
    def run(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")
        self.root.mainloop()


def main():
    CLAIApp().run()


if __name__ == "__main__":
    main()
