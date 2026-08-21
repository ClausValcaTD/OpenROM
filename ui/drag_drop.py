import os
import customtkinter as ctk
from tkinter import filedialog
from core.detector import get_extension

BG_DARK     = "#1a1a2e"
CARD_BG     = "#16213e"
ACCENT_RED  = "#e94560"
BORDER_DARK = "#333333"
TEXT_WHITE  = "#ffffff"
TEXT_GRAY   = "#a0a0b0"


class DragDropFrame(ctk.CTkFrame):
    def __init__(self, master, on_files=None, on_folder=None,
                 label="Drop ROM files here\nor click to browse",
                 accepted_exts=None, **kwargs):
        super().__init__(
            master,
            fg_color=CARD_BG,
            border_color=BORDER_DARK,
            border_width=2,
            corner_radius=12,
            height=140,
            **kwargs
        )
        self.on_files      = on_files
        self.on_folder     = on_folder
        self.label_text    = label
        self.accepted_exts = accepted_exts

        self._build()
        self._bind_drag()

    def _build(self):
        self.pack_propagate(False)
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner, text="📁",
            font=ctk.CTkFont(size=36),
            text_color=ACCENT_RED,
        ).pack(pady=(0, 4))

        lbl = ctk.CTkLabel(
            inner, text="DROP ZONE",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_WHITE,
        )
        lbl.pack()

        sub_lbl = ctk.CTkLabel(
            inner, text=self.label_text,
            font=ctk.CTkFont(size=12),
            text_color=TEXT_GRAY,
            justify="center"
        )
        sub_lbl.pack(pady=(2, 0))

        # Make clicking anywhere on the drop zone open file dialog
        for widget in (self, inner, lbl, sub_lbl):
            widget.bind("<Button-1>", lambda e: self._browse_files())
            widget.configure(cursor="hand2")

    def _browse_files(self):
        if self.accepted_exts:
            filetypes = [("ROM files", " ".join(f"*{e}" for e in self.accepted_exts))]
        else:
            filetypes = [
                ("ROM files", "*.iso *.bin *.cue *.gdi *.img *.ecm *.chd *.cso *.zso"),
                ("All files", "*.*"),
            ]
        paths = filedialog.askopenfilenames(filetypes=filetypes)
        if paths and self.on_files:
            self.on_files(list(paths))

    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if folder and self.on_folder:
            self.on_folder(folder)

    def _bind_drag(self):
        try:
            self.drop_target_register("DND_Files")    # type: ignore
            self.dnd_bind("<<Drop>>", self._on_drop)  # type: ignore
            self._set_hover_bindings()
            self._dnd_available = True
        except Exception:
            self._dnd_available = False
            self._show_dnd_unavailable()

    def _on_drop(self, event):
        raw = event.data
        import re
        paths = re.findall(r'\{[^}]+\}|[^\s]+', raw)
        paths = [p.strip("{}") for p in paths]
        valid = []
        for p in paths:
            if os.path.isdir(p) and self.on_folder:
                self.on_folder(p)
            elif os.path.isfile(p):
                ext = f".{get_extension(p)}"
                if self.accepted_exts is None or ext in self.accepted_exts:
                    valid.append(p)
        if valid and self.on_files:
            self.on_files(valid)
        self._set_normal()

    def _set_hover_bindings(self):
        try:
            self.dnd_bind("<<DragEnter>>", lambda e: self._set_hover())   # type: ignore
            self.dnd_bind("<<DragLeave>>", lambda e: self._set_normal())  # type: ignore
        except Exception:
            pass

    def _show_dnd_unavailable(self):
        """Add a small notice badge when tkinterdnd2 is not available."""
        notice = ctk.CTkLabel(
            self,
            text="⚠ Drag & Drop unavailable — use Browse",
            font=ctk.CTkFont(size=10),
            text_color="#f9a825",
            fg_color="transparent",
        )
        notice.place(relx=0.5, rely=0.92, anchor="center")

    def _set_hover(self):
        self.configure(border_color=ACCENT_RED, fg_color="#1d2a4a")

    def _set_normal(self):
        self.configure(border_color=BORDER_DARK, fg_color=CARD_BG)
