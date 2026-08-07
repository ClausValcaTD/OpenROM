import os
import subprocess
import threading
from typing import Callable
from core.detector import (
    get_chdman_path, get_tool_path, detect_file, get_valid_targets
)

# ── Compression codec map (chdman documented values only) ────────────────────
CHD_COMPRESSION = {
    "Normal": "none",
    "High":   "cdlz",
    "Max":    "cdlz,zlib,flac",   # zstd not in this chdman build; flac is confirmed
}


class ConversionJob:
    def __init__(self, filepath: str, output_dir: str,
                 target_format: str, compression: str = "High"):
        self.filepath      = filepath
        self.output_dir    = output_dir
        self.target_format = target_format   # "CHD","CSO","XISO","ECM","ISO","BIN"
        self.compression   = compression     # "Normal","High","Max"
        self.status        = "Queued"        # Queued|Converting|Done|Failed
        self.progress      = 0.0
        self.log_lines     = []
        self.error         = None
        self._temp_files   = []


class Converter:
    def __init__(self, on_log: Callable = None, on_progress: Callable = None):
        self.on_log      = on_log or (lambda msg: None)
        self.on_progress = on_progress or (lambda job, pct: None)
        self._stop_flag  = False
        self._lock       = threading.Lock()

    def stop(self):
        self._stop_flag = True

    # ── public API ────────────────────────────────────────────────────────────

    def convert(self, job: ConversionJob) -> bool:
        self._stop_flag = False
        job.status = "Converting"
        try:
            ok = self._dispatch(job)
            job.status = "Done" if ok else "Failed"
            return ok
        except Exception as e:
            job.error  = str(e)
            job.status = "Failed"
            self._log(f"[ERROR] {e}")
            return False
        finally:
            self._cleanup(job)

    def convert_batch(self, jobs: list, on_job_done: Callable = None):
        with self._lock:
            jobs_copy = list(jobs)
        for job in jobs_copy:
            if self._stop_flag:
                break
            ok = self.convert(job)
            if on_job_done:
                on_job_done(job, ok)

    # ── dispatch ──────────────────────────────────────────────────────────────

    def _dispatch(self, job: ConversionJob) -> bool:
        info = detect_file(job.filepath)
        src  = job.filepath

        if "error" in info:
            self._log(f"[ERROR] {info['error']}")
            return False

        # ECM decode first if needed
        if info.get("needs_ecm_decode"):
            src = self._unecm(job, src)
            if not src:
                return False
            info = detect_file(src)

        fmt = info.get("format", "UNKNOWN")
        tgt = job.target_format.upper()

        # ── Validate conversion is supported ──────────────────────────────────
        valid = get_valid_targets(fmt)
        if tgt not in valid:
            self._log(
                f"[ERROR] Cannot convert {fmt} → {tgt}. "
                f"Supported targets for {fmt}: {', '.join(valid) if valid else 'none'}"
            )
            return False

        # ── Route to correct handler ──────────────────────────────────────────
        # → CHD
        if tgt == "CHD":
            return self._to_chd(job, src, fmt, info)

        # CHD → ISO / BIN
        if fmt == "CHD" and tgt in ("ISO", "BIN"):
            return self._from_chd(job, src, tgt, info)

        # → CSO  (ISO only)
        if tgt == "CSO":
            return self._to_cso(job, src)

        # CSO / ZSO → ISO
        if fmt in ("CSO", "ZSO") and tgt == "ISO":
            return self._cso_to_iso(job, src)

        # → ECM  (ISO / BIN)
        if tgt == "ECM":
            return self._to_ecm(job, src)

        # ECM → ISO  (already decoded above via _unecm; just rename/move)
        # src is now the decoded BIN — rename to .iso if requested
        if fmt == "ECM" and tgt == "ISO":
            return self._move_to_iso(job, src)

        # XISO → ISO
        if fmt == "XISO" and tgt == "ISO":
            return self._xiso_to_iso(job, src)

        # ISO → XISO
        if tgt == "XISO":
            return self._to_xiso(job, src)

        self._log(f"[ERROR] Unhandled route: {fmt} → {tgt}")
        return False

    # ── CHD conversion ────────────────────────────────────────────────────────

    def _to_chd(self, job: ConversionJob, src: str, fmt: str, info: dict) -> bool:
        chdman = get_chdman_path()
        out    = self._out_path(job, src, ".chd")

        # CD-based formats → createcd; DVD/ISO → createdvd
        if fmt in ("GDI", "CUE", "BIN", "CDI", "ECM"):
            sub_cmd = "createcd"
        elif fmt in ("ISO", "IMG"):
            sub_cmd = "createdvd"
        else:
            sub_cmd = "createcd"

        cmd = [chdman, sub_cmd, "-i", src, "-o", out,
               "--compression", CHD_COMPRESSION.get(job.compression, "cdlz")]

        # BIN without CUE → generate a minimal CUE
        if fmt == "BIN" and not info.get("paired_cue"):
            cue_path = self._auto_cue(src, job.output_dir)
            if cue_path:
                job._temp_files.append(cue_path)
                # chdman needs the CUE as input, not the BIN
                idx = cmd.index(src)
                cmd[idx] = cue_path

        self._log(f"[CHD] {os.path.basename(src)} → {os.path.basename(out)}")
        return self._run(cmd, job)

    def _from_chd(self, job: ConversionJob, src: str, tgt: str, info: dict) -> bool:
        chdman   = get_chdman_path()
        chd_type = info.get("chd_type", "cd")   # 'cd' or 'dvd'

        if tgt == "BIN":
            out     = self._out_path(job, src, ".bin")
            cue_out = self._out_path(job, src, ".cue")
            if chd_type == "dvd":
                # DVD CHD → extractdvd gives ISO; BIN not meaningful, warn user
                self._log("[WARN] DVD-type CHD extracted as ISO (BIN not applicable for DVDs)")
                out = self._out_path(job, src, ".iso")
                cmd = [chdman, "extractdvd", "-i", src, "-o", out]
            else:
                cmd = [chdman, "extractcd", "-i", src, "-o", cue_out, "--outputbin", out]
        else:  # ISO
            out = self._out_path(job, src, ".iso")
            if chd_type == "dvd":
                cmd = [chdman, "extractdvd", "-i", src, "-o", out]
            else:
                cmd = [chdman, "extractcd", "-i", src, "-o", out]

        self._log(f"[EXTRACT] {os.path.basename(src)} → {os.path.basename(out)}")
        return self._run(cmd, job)

    # ── CSO conversion ────────────────────────────────────────────────────────

    def _to_cso(self, job: ConversionJob, src: str) -> bool:
        """ISO → CSO via maxcso."""
        maxcso  = get_tool_path("maxcso")
        out     = self._out_path(job, src, ".cso")
        threads = os.cpu_count() or 2
        cmd = [maxcso, f"--threads={threads}", src, "-o", out]
        if job.compression == "Max":
            cmd.insert(1, "--use-zopfli")
        elif job.compression == "High":
            cmd.insert(1, "--use-zlib")
        self._log(f"[CSO] {os.path.basename(src)} → {os.path.basename(out)}")
        return self._run(cmd, job)

    def _cso_to_iso(self, job: ConversionJob, src: str) -> bool:
        """CSO/ZSO → ISO via maxcso --decompress."""
        maxcso = get_tool_path("maxcso")
        out    = self._out_path(job, src, ".iso")
        cmd    = [maxcso, "--decompress", src, "-o", out]
        self._log(f"[CSO→ISO] {os.path.basename(src)} → {os.path.basename(out)}")
        return self._run(cmd, job)

    # ── ECM conversion ────────────────────────────────────────────────────────

    def _to_ecm(self, job: ConversionJob, src: str) -> bool:
        ecm = get_tool_path("ecm")
        out = self._out_path(job, src, os.path.splitext(src)[1] + ".ecm")
        cmd = [ecm, src, out]
        self._log(f"[ECM] {os.path.basename(src)} → {os.path.basename(out)}")
        return self._run(cmd, job)

    def _unecm(self, job: ConversionJob, src: str) -> str | None:
        """Decode ECM → raw BIN/ISO into output_dir."""
        unecm = get_tool_path("unecm")
        # strip .ecm suffix
        inner = src[:-4] if src.lower().endswith(".ecm") else src + ".bin"
        out   = os.path.join(job.output_dir, os.path.basename(inner))
        job._temp_files.append(out)
        cmd   = [unecm, src, out]
        self._log(f"[UNECM] {os.path.basename(src)} → {os.path.basename(out)}")
        ok = self._run(cmd, job)
        return out if ok else None

    def _move_to_iso(self, job: ConversionJob, src: str) -> bool:
        """After ECM decode, rename decoded file to .iso if needed."""
        out = self._out_path(job, src, ".iso")
        if src == out:
            return True
        try:
            import shutil
            shutil.move(src, out)
            # remove from temp so cleanup doesn't delete it
            if src in job._temp_files:
                job._temp_files.remove(src)
            self._log(f"[RENAME] → {os.path.basename(out)}")
            return True
        except Exception as e:
            self._log(f"[ERROR] rename failed: {e}")
            return False

    # ── XISO conversion ───────────────────────────────────────────────────────

    def _to_xiso(self, job: ConversionJob, src: str) -> bool:
        """ISO → XISO via two steps:
           1. extract-xiso -x  → extract files into a temp dir
           2. extract-xiso -c  → pack that dir into a new XISO
        extract-xiso cannot take a raw ISO directly for creation.
        """
        import shutil
        xiso     = get_tool_path("xiso")
        base     = os.path.splitext(os.path.basename(src))[0]
        tmp_dir  = os.path.join(job.output_dir, f"_xiso_tmp_{base}")
        out_name = base + ".iso"          # extract-xiso names output <dir>.iso
        out_path = os.path.join(job.output_dir, out_name)

        self._log(f"[→XISO] Step 1/2 — extracting files from ISO...")
        cmd_extract = [xiso, "-x", src, "-d", tmp_dir]
        ok = self._run(cmd_extract, job)
        if not ok:
            self._log("[→XISO] ❌ Extraction step failed")
            return False

        self._log(f"[→XISO] Step 2/2 — packing XISO from extracted files...")
        cmd_create = [xiso, "-c", tmp_dir, out_path]
        ok = self._run(cmd_create, job)

        # Always clean up temp dir
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass

        if ok:
            self._log(f"[→XISO] ✅ Created: {out_name}")
        return ok

    def _xiso_to_iso(self, job: ConversionJob, src: str) -> bool:
        """XISO → ISO via extract-xiso -r
        -r rewrites the XISO as an optimized XISO (removes padding/gaps).
        Output is a leaner .iso still readable as XISO by Xbox/emulators.
        """
        xiso = get_tool_path("xiso")
        cmd  = [xiso, "-r", src, "-d", job.output_dir]
        self._log(f"[XISO→ISO] {os.path.basename(src)} — rewriting (strip padding)...")
        return self._run(cmd, job)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _run(self, cmd: list, job: ConversionJob) -> bool:
        self._log(f"  cmd: {' '.join(os.path.basename(c) if i == 0 else c for i, c in enumerate(cmd))}")
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    self._log(f"  {line}")
                    pct = _parse_progress(line)
                    if pct is not None:
                        job.progress = pct
                        self.on_progress(job, pct)
                if self._stop_flag:
                    proc.terminate()
                    return False
            proc.wait()
            if proc.returncode == 0:
                self._log("  ✅ Done")
                job.progress = 100.0
                self.on_progress(job, 100.0)
                return True
            else:
                self._log(f"  ❌ Exit code {proc.returncode}")
                return False
        except FileNotFoundError:
            self._log(f"  ❌ Tool not found: {cmd[0]}")
            return False

    def _out_path(self, job: ConversionJob, src: str, ext: str) -> str:
        base = os.path.splitext(os.path.basename(src))[0]
        return os.path.join(job.output_dir, base + ext)

    def _log(self, msg: str):
        self.on_log(msg)

    def _cleanup(self, job: ConversionJob):
        for f in job._temp_files:
            try:
                if os.path.isfile(f):
                    os.remove(f)
            except Exception:
                pass

    def _auto_cue(self, bin_path: str, output_dir: str) -> str | None:
        """Generate minimal CUE for a single-track BIN — written to output_dir."""
        base     = os.path.splitext(os.path.basename(bin_path))[0]
        cue_path = os.path.join(output_dir, base + "_auto.cue")
        bin_name = os.path.basename(bin_path)
        try:
            with open(cue_path, "w") as f:
                f.write(f'FILE "{bin_name}" BINARY\n')
                f.write("  TRACK 01 MODE2/2352\n")
                f.write("    INDEX 01 00:00:00\n")
            return cue_path
        except Exception as e:
            self._log(f"[WARN] Could not write auto CUE: {e}")
            return None


def _parse_progress(line: str) -> float | None:
    import re
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
    if m:
        return float(m.group(1))
    return None
