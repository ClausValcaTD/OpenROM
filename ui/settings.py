import os
import platform
import urllib.request
import json
import threading
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

CURRENT_VERSION = "2.0.0"
GITHUB_API_URL  = "https://api.github.com/repos/M5Devs/OpenROM/releases/latest"


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("OpenROM — Settings")
        self.geometry("560x580")
        self.resizable(False, False)
        self.configure(fg_color=NAVY)
        self.grab_set()

        self.config = load_config()
        self.entries = {}

        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Settings",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=CYAN).pack(pady=(16, 8))

        frame = ctk.CTkFrame(self, fg_color=DARK2, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=16, pady=8)

        # Appearance
        self._row(frame, "Appearance",
                  ctk.CTkOptionMenu(frame, values=["Dark", "Light", "System"],
                                    fg_color=DARK3, button_color=CYAN2,
                                    command=lambda v: ctk.set_appearance_mode(v.lower())))

        # macOS info banner
        if platform.system() == "Darwin":
            mac_info = ctk.CTkLabel(
                frame,
                text="ℹ️  macOS: install missing tools via  brew install chdman maxcso",
                font=ctk.CTkFont(size=11),
                text_color=CYAN2,
                fg_color=DARK3,
                corner_radius=6,
            )
            mac_info.pack(fill="x", padx=16, pady=(8, 0))

        # Tool paths
        ctk.CTkLabel(frame,
                     text="External Tool Paths (blank = bundled / system PATH)",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=CYAN2).pack(fill="x", padx=16, pady=(15, 5))

        for key, label in [
            ("chdman", "CHDMan Path:"),
            ("maxcso", "MaxCSO Path:"),
            ("ecm",    "ECM Path:"),
            ("unecm",  "UNECM Path:"),
            ("xiso",   "Extract-XISO Path:"),
        ]:
            self._tool_row(frame, label, key)

        # Update button
        self._update_btn = ctk.CTkButton(
            frame, text="Check for Updates",
            fg_color=DARK3, hover_color=DARK2,
            text_color=CYAN2, height=32,
            command=self._check_updates,
        )
        self._update_btn.pack(fill="x", padx=16, pady=6)

        # Save / Cancel
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=12, padx=16, fill="x")

        ctk.CTkButton(btn_row, text="Save Settings", height=38,
                      fg_color=CYAN2, hover_color=CYAN,
                      text_color=NAVY, font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._save_settings
                      ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(btn_row, text="Cancel", height=38,
                      fg_color=DARK3, hover_color=DARK2,
                      text_color=GRAY,
                      command=self.destroy
                      ).pack(side="right", width=120)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _row(self, parent, label, widget):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(row, text=label, text_color=GRAY,
                     font=ctk.CTkFont(size=12)).pack(side="left")
        widget.pack(side="right")

    def _tool_row(self, parent, label, key):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=4)

        ctk.CTkLabel(row, text=label, text_color=GRAY,
                     font=ctk.CTkFont(size=11), width=120, anchor="w").pack(side="left")

        entry = ctk.CTkEntry(row, fg_color=DARK3, border_color=CYAN2,
                             text_color=WHITE, font=ctk.CTkFont(size=11))
        entry.insert(0, self.config.get(key, ""))
        entry.pack(side="left", fill="x", expand=True, padx=(4, 4))
        self.entries[key] = entry

        def browse(e=entry):
            fp = filedialog.askopenfilename()
            if fp:
                e.delete(0, "end")
                e.insert(0, fp)

        ctk.CTkButton(row, text="Browse", width=60, height=26,
                      fg_color=DARK3, hover_color=DARK2, text_color=CYAN2,
                      font=ctk.CTkFont(size=10), command=browse).pack(side="right")

    def _save_settings(self):
        for key, entry in self.entries.items():
            self.config[key] = entry.get().strip()
        save_config(self.config)
        messagebox.showinfo("Success", "Settings saved successfully!")
        self.destroy()

    # ── real update check via GitHub API ──────────────────────────────────────

    def _check_updates(self):
        self._update_btn.configure(text="Checking…", state="disabled")
        threading.Thread(target=self._fetch_latest, daemon=True).start()

    def _fetch_latest(self):
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={"User-Agent": f"OpenROM/{CURRENT_VERSION}"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
            latest = data.get("tag_name", "").lstrip("v")
            url    = data.get("html_url", "https://github.com/M5Devs/OpenROM/releases")
            self.after(0, lambda: self._show_update_result(latest, url))
        except Exception as e:
            self.after(0, lambda: self._show_update_result(None, None, error=str(e)))

    def _show_update_result(self, latest: str | None, url: str | None, error: str = ""):
        self._update_btn.configure(text="Check for Updates", state="normal")
        if error:
            messagebox.showerror("Update Check Failed",
                                 f"Could not reach GitHub:\n{error}")
            return
        if latest and latest != CURRENT_VERSION:
            if messagebox.askyesno("Update Available",
                                   f"New version v{latest} is available!\n"
                                   f"You have v{CURRENT_VERSION}.\n\nOpen release page?"):
                import webbrowser
                webbrowser.open(url)
        else:
            messagebox.showinfo("Up to Date",
                                f"You're running the latest version (v{CURRENT_VERSION}).")
