import os
import customtkinter as ctk
from tkinter import filedialog

NAVY  = "#0d1b2a"
CYAN  = "#00e5ff"
CYAN2 = "#00b4cc"
DARK2 = "#112233"
DARK3 = "#0a1628"
GRAY  = "#7a8a9a"
WHITE = "#e0f0ff"


class DragDropFrame(ctk.CTkFrame):
    def __init__(self, master, on_files=None, on_folder=None,
                 label="Drag ISO / BIN / CUE / GDI / ECM files here  —  or  Browse",
                 accepted_exts=None, **kwargs):
        super().__init__(master, fg_color=DARK3,
                         border_color=CYAN2, border_width=1,
                         corner_radius=10, height=90, **kwargs)
        self.on_files      = on_files
        self.on_folder     = on_folder
        self.label_text    = label
        self.accepted_exts = accepted_exts  # None = all supported

        self._build()
        self._bind_drag()

    def _build(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner, text="📂",
            font=ctk.CTkFont(size=28),
            text_color=CYAN2,
        ).pack()

        ctk.CTkLabel(
            inner, text=self.label_text,
            font=ctk.CTkFont(size=12),
            text_color=GRAY,
        ).pack()

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(pady=(6, 0))

        ctk.CTkButton(
            btn_row, text="Browse Files", width=110, height=28,
            fg_color=CYAN2, hover_color=CYAN,
            text_color=NAVY, font=ctk.CTkFont(size=11, weight="bold"),
            command=self._browse_files,
        ).pack(side="left", padx=4)

        if self.on_folder:
            ctk.CTkButton(
                btn_row, text="Browse Folder", width=110, height=28,
                fg_color=DARK2, hover_color=DARK3,
                text_color=CYAN2, font=ctk.CTkFont(size=11),
                command=self._browse_folder,
            ).pack(side="left", padx=4)

    def _browse_files(self):
        if self.accepted_exts:
            filetypes = [("ROM files", " ".join(f"*{e}" for e in self.accepted_exts))]
        else:
            filetypes = [
                ("ROM files", "*.iso *.bin *.cue *.gdi *.img *.ecm *.chd *.cso *.zso"),
                ("All files",  "*.*"),
            ]
        paths = filedialog.askopenfilenames(filetypes=filetypes)
        if paths and self.on_files:
            self.on_files(list(paths))

    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if folder and self.on_folder:
            self.on_folder(folder)

    def _bind_drag(self):
        """
        Native tkinter drag-and-drop via TkinterDnD2 if available,
        otherwise silently skip (Browse buttons still work).
        """
        try:
            self.drop_target_register("DND_Files")   # type: ignore
            self.dnd_bind("<<Drop>>", self._on_drop)  # type: ignore
            self._set_hover_bindings()
        except Exception:
            pass

    def _on_drop(self, event):
        raw = event.data
        # TkinterDnD2 returns paths wrapped in {} for paths with spaces
        import re
        paths = re.findall(r'\{[^}]+\}|[^\s]+', raw)
        paths = [p.strip("{}") for p in paths]
        valid = []
        for p in paths:
            if os.path.isdir(p) and self.on_folder:
                self.on_folder(p)
            elif os.path.isfile(p):
                ext = os.path.splitext(p)[1].lower()
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

    def _set_hover(self):
        self.configure(border_color=CYAN, fg_color="#0e2030")

    def _set_normal(self):
        self.configure(border_color=CYAN2, fg_color=DARK3)
