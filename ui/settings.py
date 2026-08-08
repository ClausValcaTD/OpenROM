import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from core.config import load_config, save_config

NAVY  = "#0d1b2a"
CYAN  = "#00e5ff"
CYAN2 = "#00b4cc"
DARK2 = "#112233"
DARK3 = "#0a1628"
GRAY  = "#7a8a9a"
WHITE = "#e0f0ff"

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("OpenROM — Settings")
        self.geometry("560x540")
        self.resizable(False, False)
        self.configure(fg_color=NAVY)
        self.grab_set()

        # Load configuration
        self.config = load_config()
        self.entries = {}

        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Settings",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=CYAN).pack(pady=(16, 8))

        frame = ctk.CTkFrame(self, fg_color=DARK2, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=16, pady=8)

        # Theme Section
        self._row(frame, "Appearance",
                  ctk.CTkOptionMenu(frame, values=["Dark", "Light", "System"],
                                    fg_color=DARK3, button_color=CYAN2,
                                    command=lambda v: ctk.set_appearance_mode(v.lower())))

        # Tool Paths Section
        tools_label = ctk.CTkLabel(frame, text="External Tool Paths (blank for bundled/default)",
                                   font=ctk.CTkFont(size=12, weight="bold"),
                                   text_color=CYAN2)
        tools_label.pack(fill="x", padx=16, pady=(15, 5))

        tools_keys = [
            ("chdman", "CHDMan Path:"),
            ("maxcso", "MaxCSO Path:"),
            ("ecm", "ECM Path:"),
            ("unecm", "UNECM Path:"),
            ("xiso", "Extract-XISO Path:")
        ]

        for key, label in tools_keys:
            self._tool_row(frame, label, key)

        # Check for updates placeholder
        ctk.CTkButton(
            frame, text="Check for Updates",
            fg_color=DARK3, hover_color=DARK2,
            text_color=CYAN2, height=32,
            command=self._check_updates,
        ).pack(fill="x", padx=16, pady=6)

        # Save & Cancel Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=12, padx=16, fill="x")

        ctk.CTkButton(
            btn_row, text="Save Settings", height=38,
            fg_color=CYAN2, hover_color=CYAN,
            text_color=NAVY, font=ctk.CTkFont(size=12, weight="bold"),
            command=self._save_settings,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btn_row, text="Cancel", height=38,
            fg_color=DARK3, hover_color=DARK2,
            text_color=GRAY,
            command=self.destroy,
        ).pack(side="right", width=120)

    def _row(self, parent, label, widget):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(row, text=label, text_color=GRAY,
                     font=ctk.CTkFont(size=12)).pack(side="left")
        widget.pack(side="right")

    def _tool_row(self, parent, label, key):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=4)

        lbl = ctk.CTkLabel(row, text=label, text_color=GRAY,
                           font=ctk.CTkFont(size=11), width=120, anchor="w")
        lbl.pack(side="left")

        entry = ctk.CTkEntry(row, fg_color=DARK3, border_color=CYAN2, text_color=WHITE, font=ctk.CTkFont(size=11))
        entry.insert(0, self.config.get(key, ""))
        entry.pack(side="left", fill="x", expand=True, padx=(4, 4))
        self.entries[key] = entry

        def browse():
            filepath = filedialog.askopenfilename()
            if filepath:
                entry.delete(0, "end")
                entry.insert(0, filepath)

        btn = ctk.CTkButton(row, text="Browse", width=60, height=26,
                            fg_color=DARK3, hover_color=DARK2, text_color=CYAN2,
                            font=ctk.CTkFont(size=10), command=browse)
        btn.pack(side="right")

    def _save_settings(self):
        for key, entry in self.entries.items():
            self.config[key] = entry.get().strip()
        save_config(self.config)
        messagebox.showinfo("Success", "Settings saved successfully!")
        self.destroy()

    def _check_updates(self):
        messagebox.showinfo("Update Check", "You are running the latest version (v1.0.0).")
