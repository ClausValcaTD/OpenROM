import os
import threading
import customtkinter as ctk
from tkinter import filedialog, StringVar
from ui.drag_drop import DragDropFrame
from ui.settings import SettingsWindow
from core.detector import detect_file, detect_folder, SUPPORTED_INPUT, get_valid_targets
from core.converter import Converter, ConversionJob
from core.validator import verify_chd

# ── Theme ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

NAVY   = "#0d1b2a"
CYAN   = "#00e5ff"
CYAN2  = "#00b4cc"
DARK2  = "#112233"
DARK3  = "#0a1628"
WHITE  = "#e0f0ff"
GRAY   = "#7a8a9a"
GREEN  = "#00e676"
RED    = "#ff5252"
AMBER  = "#ffab40"

# All possible output formats shown in the UI
ALL_FORMATS = ["CHD", "ISO", "BIN", "CSO", "ECM", "XISO"]


class MainWindow(ctk.CTk):
    def __init__(self):

        super().__init__()
        self.title("OpenROM  |  M5 Dev")
        self.geometry("960x700")
        self.minsize(800, 600)
        self.configure(fg_color=NAVY)

        # State
        self._jobs_lock  = threading.Lock()
        self.jobs: list[ConversionJob] = []
        self.job_rows: dict = {}          # filepath → row widgets
        self.output_dir  = StringVar(value="")
        self.same_as_src = ctk.BooleanVar(value=True)
        self.compression = StringVar(value="High")
        self.target_fmt  = StringVar(value="CHD")
        self.delete_src  = ctk.BooleanVar(value=False)
        self.verify_after= ctk.BooleanVar(value=True)
        self._converting = False
        self.converter   = Converter(
            on_log=self._append_log,
            on_progress=self._on_progress,
        )

        self._build_ui()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=DARK3, height=56, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr, text="⬡  OpenROM",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=CYAN,
        ).pack(side="left", padx=20, pady=12)
        ctk.CTkLabel(
            hdr, text="Universal ROM Compression Suite  |  M5 Dev",
            font=ctk.CTkFont(size=12),
            text_color=GRAY,
        ).pack(side="left", pady=12)

        ctk.CTkButton(
            hdr, text="⚙", width=40, height=32,
            fg_color="transparent", text_color=GRAY,
            hover_color=DARK2,
            command=self._open_settings,
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            hdr, text="☕ Ko-fi", width=80, height=32,
            fg_color="#FF5E5B", hover_color="#cc4a47",
            text_color="white",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._open_url("https://ko-fi.com/m5dev"),
        ).pack(side="right", padx=4)

        # Tabs
        tabs = ctk.CTkTabview(
            self, fg_color=DARK2,
            segmented_button_fg_color=DARK3,
            segmented_button_selected_color=CYAN2,
            segmented_button_unselected_color=DARK3,
            segmented_button_selected_hover_color=CYAN,
        )
        tabs.pack(fill="both", expand=True, padx=12, pady=(8, 0))
        tabs.add("  Compress  ")
        tabs.add("  Extract  ")

        self._build_compress_tab(tabs.tab("  Compress  "))
        self._build_extract_tab(tabs.tab("  Extract  "))

        # Log
        log_frame = ctk.CTkFrame(self, fg_color=DARK3, corner_radius=0, height=150)
        log_frame.pack(fill="x", side="bottom")
        log_frame.pack_propagate(False)

        log_hdr = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_hdr.pack(fill="x", padx=8, pady=(4, 0))
        ctk.CTkLabel(log_hdr, text="Operation Log",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=CYAN).pack(side="left")
        ctk.CTkButton(log_hdr, text="Clear", width=50, height=22,
                      fg_color="transparent", text_color=GRAY,
                      hover_color=DARK2,
                      command=self._clear_log).pack(side="right")

        self.log_box = ctk.CTkTextbox(
            log_frame, fg_color=DARK3, text_color=CYAN2,
            font=ctk.CTkFont(family="Consolas", size=11),
            border_width=0,
        )
        self.log_box.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        self._append_log("> OpenROM initialized  —  M5 Dev Edition")
        self._append_log("> Drop your ROM files or use Browse to get started")

    # ── Compress Tab ──────────────────────────────────────────────────────────

    def _build_compress_tab(self, parent):
        self.drop_frame = DragDropFrame(
            parent,
            on_files=self._add_files,
            on_folder=self._add_folder,
        )
        self.drop_frame.pack(fill="x", padx=8, pady=8)

        # File list
        list_frame = ctk.CTkFrame(parent, fg_color=DARK2)
        list_frame.pack(fill="both", expand=True, padx=8)

        hdr = ctk.CTkFrame(list_frame, fg_color=DARK3, height=28)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        for text, width in [("File Name", 280), ("Fmt", 70),
                             ("Size", 80), ("Valid Targets", 160), ("Status", 120)]:
            ctk.CTkLabel(hdr, text=text, width=width,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=GRAY, anchor="w").pack(side="left", padx=6)

        self.file_list = ctk.CTkScrollableFrame(
            list_frame, fg_color=DARK2, height=180)
        self.file_list.pack(fill="both", expand=True)

        # Settings row
        settings_row = ctk.CTkFrame(parent, fg_color="transparent")
        settings_row.pack(fill="x", padx=8, pady=6)

        ctk.CTkLabel(settings_row, text="Convert to:",
                     text_color=GRAY, font=ctk.CTkFont(size=12)).pack(side="left")
        self._fmt_buttons = {}
        for fmt in ALL_FORMATS:
            rb = ctk.CTkRadioButton(
                settings_row, text=fmt, variable=self.target_fmt, value=fmt,
                text_color=WHITE, fg_color=CYAN2,
                font=ctk.CTkFont(size=12),
            )
            rb.pack(side="left", padx=6)
            self._fmt_buttons[fmt] = rb

        ctk.CTkLabel(settings_row, text="  Compression:",
                     text_color=GRAY, font=ctk.CTkFont(size=12)).pack(side="left", padx=(16, 0))
        for lvl in ["Normal", "High", "Max"]:
            ctk.CTkRadioButton(
                settings_row, text=lvl, variable=self.compression, value=lvl,
                text_color=WHITE, fg_color=CYAN2,
                font=ctk.CTkFont(size=12),
            ).pack(side="left", padx=6)

        # Output row
        out_row = ctk.CTkFrame(parent, fg_color="transparent")
        out_row.pack(fill="x", padx=8, pady=(0, 4))

        ctk.CTkLabel(out_row, text="Output:",
                     text_color=GRAY, font=ctk.CTkFont(size=12)).pack(side="left")
        self.out_entry = ctk.CTkEntry(
            out_row, textvariable=self.output_dir,
            fg_color=DARK3, border_color=CYAN2,
            text_color=WHITE, width=320, state="disabled",
        )
        self.out_entry.pack(side="left", padx=6)
        ctk.CTkButton(
            out_row, text="📁", width=36, height=28,
            fg_color=DARK3, hover_color=DARK2, text_color=CYAN,
            command=self._browse_output,
        ).pack(side="left")
        ctk.CTkCheckBox(
            out_row, text="Same as source",
            variable=self.same_as_src,
            text_color=GRAY, fg_color=CYAN2,
            font=ctk.CTkFont(size=12),
            command=self._toggle_same_src,
        ).pack(side="left", padx=12)
        ctk.CTkCheckBox(
            out_row, text="Delete source after",
            variable=self.delete_src,
            text_color=GRAY, fg_color=CYAN2,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=8)
        ctk.CTkCheckBox(
            out_row, text="Verify CHD after",
            variable=self.verify_after,
            text_color=GRAY, fg_color=CYAN2,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=8)

        # Start / progress
        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(4, 8))

        self.start_btn = ctk.CTkButton(
            btn_row, text="▶  START CONVERSION",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=CYAN2, hover_color=CYAN,
            text_color=NAVY, height=42,
            command=self._start_conversion,
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="✖ Clear All", width=100, height=42,
            fg_color=DARK3, hover_color=DARK2, text_color=GRAY,
            command=self._clear_all,
        ).pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(
            parent, fg_color=DARK3, progress_color=CYAN2)
        self.progress_bar.pack(fill="x", padx=8, pady=(0, 4))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            parent, text="Queue: 0 files  |  Status: Idle",
            text_color=GRAY, font=ctk.CTkFont(size=11))
        self.status_label.pack(anchor="e", padx=8)

    # ── Extract Tab ───────────────────────────────────────────────────────────

    def _build_extract_tab(self, parent):
        ctk.CTkLabel(
            parent,
            text="Drop a .chd file to extract it back to ISO / BIN+CUE",
            text_color=GRAY, font=ctk.CTkFont(size=13),
        ).pack(pady=20)

        self.ext_drop = DragDropFrame(
            parent,
            on_files=self._extract_files,
            on_folder=None,
            label="Drop .CHD files here or Browse",
            accepted_exts=[".chd"],
        )
        self.ext_drop.pack(fill="x", padx=8)

        fmt_row = ctk.CTkFrame(parent, fg_color="transparent")
        fmt_row.pack(pady=12)
        ctk.CTkLabel(fmt_row, text="Extract to:",
                     text_color=GRAY).pack(side="left", padx=8)
        self.ext_fmt = StringVar(value="ISO")
        for fmt in ["ISO", "BIN"]:
            ctk.CTkRadioButton(
                fmt_row, text=fmt, variable=self.ext_fmt, value=fmt,
                text_color=WHITE, fg_color=CYAN2,
            ).pack(side="left", padx=8)

        self.ext_btn = ctk.CTkButton(
            parent, text="▶  START EXTRACTION",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=CYAN2, hover_color=CYAN,
            text_color=NAVY, height=42,
            command=self._start_extraction,
        )
        self.ext_btn.pack(padx=8, pady=8, fill="x")
        self.ext_files: list = []

    # ── File management ───────────────────────────────────────────────────────

    def _add_files(self, paths: list):
        with self._jobs_lock:
            existing = {j.filepath for j in self.jobs}
        for p in paths:
            ext = os.path.splitext(p)[1].lower()
            if ext not in SUPPORTED_INPUT or p in existing:
                continue
            info = detect_file(p)
            valid = info.get("valid_targets", [])
            if not valid:
                self._append_log(f"[SKIP] {os.path.basename(p)} — no valid conversion targets")
                continue
            # Pick first valid target as default
            default_fmt = valid[0] if self.target_fmt.get() not in valid else self.target_fmt.get()
            job = ConversionJob(
                filepath=p,
                output_dir="",
                target_format=default_fmt,
                compression=self.compression.get(),
            )
            with self._jobs_lock:
                self.jobs.append(job)
                existing.add(p)
            self._add_row(job, info, valid)
        self._update_status()

    def _add_folder(self, folder: str):
        files = detect_folder(folder)
        paths = [f["filepath"] for f in files]
        self._add_files(paths)

    def _add_row(self, job: ConversionJob, info: dict, valid_targets: list):
        row = ctk.CTkFrame(self.file_list, fg_color=DARK3, height=34)
        row.pack(fill="x", pady=1)

        ctk.CTkLabel(
            row, text=os.path.basename(job.filepath)[:38],
            width=280, anchor="w",
            text_color=WHITE, font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=6)

        ctk.CTkLabel(
            row, text=info.get("format", "?"),
            width=70, anchor="w",
            text_color=CYAN, font=ctk.CTkFont(size=11),
        ).pack(side="left")

        ctk.CTkLabel(
            row, text=info.get("size_str", "?"),
            width=80, anchor="w",
            text_color=GRAY, font=ctk.CTkFont(size=11),
        ).pack(side="left")

        # Inline target format selector — only shows valid options
        fmt_var = StringVar(value=job.target_format)

        def _on_fmt_change(val, j=job, v=fmt_var):
            j.target_format = val

        fmt_menu = ctk.CTkOptionMenu(
            row,
            values=valid_targets,
            variable=fmt_var,
            command=_on_fmt_change,
            fg_color=DARK2, button_color=CYAN2,
            dropdown_fg_color=DARK3,
            text_color=WHITE,
            width=150, height=24,
            font=ctk.CTkFont(size=11),
        )
        fmt_menu.pack(side="left", padx=4)

        status_lbl = ctk.CTkLabel(
            row, text="Queued",
            width=120, anchor="w",
            text_color=AMBER, font=ctk.CTkFont(size=11),
        )
        status_lbl.pack(side="left")

        prog = ctk.CTkProgressBar(row, width=80, height=10,
                                   fg_color=DARK2, progress_color=CYAN2)
        prog.pack(side="left", padx=4)
        prog.set(0)

        self.job_rows[job.filepath] = {
            "row": row, "status": status_lbl, "progress": prog,
        }

    def _clear_all(self):
        if self._converting:
            return
        with self._jobs_lock:
            self.jobs.clear()
        self.job_rows.clear()
        for w in self.file_list.winfo_children():
            w.destroy()
        self._update_status()

    # ── Conversion ────────────────────────────────────────────────────────────

    def _start_conversion(self):
        with self._jobs_lock:
            queued = [j for j in self.jobs if j.status == "Queued"]
        if self._converting or not queued:
            return
        self._converting = True
        self.start_btn.configure(
            text="⏹  STOP", fg_color=RED,
            command=self._stop_conversion)

        def run():
            with self._jobs_lock:
                jobs_snap = list(self.jobs)
            for job in jobs_snap:
                if self.converter._stop_flag:
                    break
                if job.status != "Queued":
                    continue

                # Resolve output dir
                if self.same_as_src.get():
                    job.output_dir = os.path.dirname(job.filepath)
                else:
                    job.output_dir = self.output_dir.get() or os.path.dirname(job.filepath)

                job.compression = self.compression.get()
                self._set_row_status(job.filepath, "Converting...", CYAN)

                ok = self.converter.convert(job)

                if ok:
                    self._set_row_status(job.filepath, "✅ Done", GREEN)
                    if self.verify_after.get() and job.target_format == "CHD":
                        out = os.path.join(
                            job.output_dir,
                            os.path.splitext(os.path.basename(job.filepath))[0] + ".chd"
                        )
                        verify_chd(out, on_log=self._append_log)
                    if self.delete_src.get():
                        try:
                            os.remove(job.filepath)
                        except Exception:
                            pass
                else:
                    self._set_row_status(job.filepath, "❌ Failed", RED)

            self._converting = False
            self.after(0, self._conversion_done)

        threading.Thread(target=run, daemon=True).start()

    def _stop_conversion(self):
        self.converter.stop()
        self._converting = False
        self._conversion_done()

    def _conversion_done(self):
        self.start_btn.configure(
            text="▶  START CONVERSION",
            fg_color=CYAN2,
            command=self._start_conversion,
        )
        self.progress_bar.set(1.0)
        self._update_status()
        self._append_log("> All jobs finished")

    def _set_row_status(self, filepath: str, text: str, color: str):
        def _do():
            row = self.job_rows.get(filepath)
            if row:
                row["status"].configure(text=text, text_color=color)
        self.after(0, _do)

    def _on_progress(self, job: ConversionJob, pct: float):
        def _do():
            row = self.job_rows.get(job.filepath)
            if row:
                row["progress"].set(pct / 100)
            with self._jobs_lock:
                total = len(self.jobs)
                done  = sum(1 for j in self.jobs if j.status == "Done")
            if total:
                self.progress_bar.set(done / total)
        self.after(0, _do)

    # ── Extraction ────────────────────────────────────────────────────────────

    def _extract_files(self, paths: list):
        self.ext_files = [p for p in paths if p.lower().endswith(".chd")]
        self._append_log(f"> {len(self.ext_files)} CHD file(s) queued for extraction")

    def _start_extraction(self):
        if not self.ext_files:
            return

        def run():
            for fp in self.ext_files:
                info = detect_file(fp)
                job = ConversionJob(
                    filepath=fp,
                    output_dir=os.path.dirname(fp),
                    target_format=self.ext_fmt.get(),
                    compression="Normal",
                )
                self.converter.convert(job)
            self._append_log("> Extraction complete")

        threading.Thread(target=run, daemon=True).start()

    # ── UI helpers ────────────────────────────────────────────────────────────

    def _browse_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_dir.set(folder)
            self.same_as_src.set(False)
            self.out_entry.configure(state="normal")

    def _toggle_same_src(self):
        if self.same_as_src.get():
            self.out_entry.configure(state="disabled")
        else:
            self.out_entry.configure(state="normal")

    def _append_log(self, msg: str):
        def _do():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _do)

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _update_status(self):
        with self._jobs_lock:
            total = len(self.jobs)
            done  = sum(1 for j in self.jobs if j.status == "Done")
        self.status_label.configure(
            text=f"Queue: {total} file(s)  |  Done: {done}  |  "
                 f"Status: {'Converting...' if self._converting else 'Idle'}"
        )

    def _open_settings(self):
        SettingsWindow(self)

    def _open_url(self, url: str):
        import webbrowser
        webbrowser.open(url)
