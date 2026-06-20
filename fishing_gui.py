import os
import threading
import tkinter as tk
from tkinter import messagebox

import keyboard

from fishing_macro import FishingMacro, START_KEY, STOP_KEY, is_admin


APP_TITLE = "EpicGamesLauncher"
BG = "#242424"
TITLE_BG = "#050505"
PANEL = "#19192d"
PANEL_BORDER = "#2b2b50"
BUTTON_DARK = "#333333"
BUTTON_DISABLED = "#353535"
START_BLUE = "#0b9dcc"
STOP_RED = "#d54848"
GREEN = "#42c64f"
TEXT = "#f4f4f4"
MUTED = "#b7b7b7"
ACCENT = "#00a6ff"


class FishingMacroGui:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("399x187")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.macro = FishingMacro()
        self.status_text = tk.StringVar(value="• ระบบพร้อม (สลับไปจอเกมแล้วกด F9)")
        self.bait_text = tk.StringVar(value="เหยื่อ V6")

        self._build_titlebar()
        self._build_body()
        self._register_hotkeys()
        self._poll_status()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_titlebar(self):
        titlebar = tk.Frame(self.root, bg=TITLE_BG, height=29)
        titlebar.pack(fill="x")
        titlebar.pack_propagate(False)

        tk.Label(
            titlebar,
            text="EPIC",
            bg=TITLE_BG,
            fg=TEXT,
            font=("Segoe UI", 6, "bold"),
            width=4,
        ).pack(side="left", padx=(7, 3), pady=6)

        tk.Label(
            titlebar,
            text=APP_TITLE,
            bg=TITLE_BG,
            fg=TEXT,
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")

        title_actions = (
            ("×", self.on_close),
            ("□", None),
            ("—", self.root.iconify),
        )
        for symbol, command in title_actions:
            widget = tk.Button(
                titlebar,
                text=symbol,
                bg=TITLE_BG,
                fg=TEXT,
                activebackground=TITLE_BG,
                activeforeground=TEXT,
                font=("Segoe UI", 12),
                width=4,
                relief="flat",
                bd=0,
                command=command,
                cursor="hand2" if command else "arrow",
            )
            widget.pack(side="right")

    def _build_body(self):
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=(10, 12))

        top = tk.Frame(body, bg=BG)
        top.pack(fill="x")

        self._button(top, "⚙ Settings", BUTTON_DARK, self.open_settings, width=10).pack(side="left")
        self._button(top, self.bait_text, GREEN, self.refresh_bait_label, width=8).pack(side="left", padx=(10, 0))
        self._button(top, "⎋ Logout", STOP_RED, self.stop_macro, width=8).pack(side="left", padx=(10, 0))
        self._button(top, "☠", BUTTON_DARK, None, width=3).pack(side="left", padx=(8, 0))
        self._button(top, "☀", BUTTON_DARK, self.toggle_topmost, width=3).pack(side="right")

        status = tk.Frame(body, bg=PANEL, highlightbackground=PANEL_BORDER, highlightthickness=1, height=40)
        status.pack(fill="x", pady=(11, 10))
        status.pack_propagate(False)

        tk.Label(
            status,
            textvariable=self.status_text,
            bg=PANEL,
            fg=ACCENT,
            font=("Segoe UI", 9, "bold"),
        ).pack(expand=True)

        actions = tk.Frame(body, bg=BG)
        actions.pack(fill="x")

        self.start_btn = self._button(actions, f"START ({START_KEY})", START_BLUE, self.start_macro, width=17, height=2)
        self.start_btn.pack(side="left", fill="x", expand=True)

        self.stop_btn = self._button(actions, f"STOP ({STOP_KEY})", BUTTON_DISABLED, self.stop_macro, width=17, height=2)
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(11, 0))

    def _button(self, parent, text, bg, command, width=8, height=1):
        textvariable = text if isinstance(text, tk.StringVar) else None
        label = "" if textvariable else text
        return tk.Button(
            parent,
            text=label,
            textvariable=textvariable,
            command=command,
            width=width,
            height=height,
            bg=bg,
            fg=TEXT,
            activebackground=bg,
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )

    def _register_hotkeys(self):
        keyboard.on_press_key(START_KEY, lambda _: self.root.after(0, self.start_macro), suppress=False)
        keyboard.on_press_key(STOP_KEY, lambda _: self.root.after(0, self.stop_macro), suppress=False)

    def start_macro(self):
        self.macro.start()
        self._sync_buttons()

    def stop_macro(self):
        self.macro.stop()
        self._sync_buttons()

    def open_settings(self):
        messagebox.showinfo(
            "Settings",
            "ปรับค่าหลักได้ใน fishing_macro.py\nอัดจังหวะเหวี่ยงเบ็ดได้จาก record_cast.bat",
        )

    def refresh_bait_label(self):
        self.bait_text.set("เหยื่อ V6")

    def toggle_topmost(self):
        current = bool(self.root.attributes("-topmost"))
        self.root.attributes("-topmost", not current)

    def _sync_buttons(self):
        if self.macro.running:
            self.status_text.set(f"• กำลังทำงาน | รอบ {self.macro.round_count} | ปลา {self.macro.fish_count}")
            self.start_btn.configure(bg=BUTTON_DISABLED, activebackground=BUTTON_DISABLED, fg=MUTED)
            self.stop_btn.configure(bg=STOP_RED, activebackground=STOP_RED, fg=TEXT)
        else:
            self.status_text.set(f"• ระบบพร้อม (สลับไปจอเกมแล้วกด {START_KEY})")
            self.start_btn.configure(bg=START_BLUE, activebackground=START_BLUE, fg=TEXT)
            self.stop_btn.configure(bg=BUTTON_DISABLED, activebackground=BUTTON_DISABLED, fg=MUTED)

    def _poll_status(self):
        self._sync_buttons()
        self.root.after(500, self._poll_status)

    def on_close(self):
        self.macro.stop()
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        if not is_admin():
            messagebox.showwarning(
                "Administrator recommended",
                "ควรรันแบบ Administrator เพื่อให้ส่งปุ่มเข้าเกมได้เสถียร",
            )
        self.root.mainloop()


def main():
    os.system("")
    app = FishingMacroGui()
    app.run()


if __name__ == "__main__":
    main()
