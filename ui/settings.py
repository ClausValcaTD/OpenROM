import customtkinter as ctk

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
        self.geometry("420x360")
        self.resizable(False, False)
        self.configure(fg_color=NAVY)
        self.grab_set()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Settings",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=CYAN).pack(pady=(16, 8))

        frame = ctk.CTkFrame(self, fg_color=DARK2, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=16, pady=8)

        # Theme
        self._row(frame, "Appearance",
                  ctk.CTkOptionMenu(frame, values=["Dark", "Light", "System"],
                                    fg_color=DARK3, button_color=CYAN2,
                                    command=lambda v: ctk.set_appearance_mode(v.lower())))

        # Check for updates placeholder
        ctk.CTkButton(
            frame, text="Check for Updates",
            fg_color=DARK3, hover_color=DARK2,
            text_color=CYAN2, height=32,
            command=lambda: None,
        ).pack(fill="x", padx=16, pady=6)

        # About
        ctk.CTkLabel(
            frame,
            text="OpenROM v1.0.0  —  GPL v3\nM5 Dev  |  github.com/M5Dev/OpenROM",
            text_color=GRAY, font=ctk.CTkFont(size=11),
        ).pack(pady=12)

        ctk.CTkButton(
            self, text="Close", height=36,
            fg_color=CYAN2, hover_color=CYAN,
            text_color=NAVY,
            command=self.destroy,
        ).pack(pady=8, padx=16, fill="x")

    def _row(self, parent, label, widget):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(row, text=label, text_color=GRAY,
                     font=ctk.CTkFont(size=12)).pack(side="left")
        widget.pack(side="right")
