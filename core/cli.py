"""
OpenROM CLI — Universal ROM Compression Suite
M5 Dev | GPL v3 + Commons Clause

Usage examples:
  openrom --input game.iso --format CHD
  openrom --input game.iso --format CHD --compression High --verify
  openrom --input game.iso --format CHD --output /path/to/folder
  openrom --folder /roms/ --format CHD --compression Max
  openrom --input game.chd --verify-only
  openrom --list-formats
"""

import sys
import os
import argparse
import threading

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.detector import detect_file, detect_folder, CONVERSION_MAP, get_valid_targets
from core.converter import Converter, ConversionJob
from core.validator import verify_chd

# ── ANSI colors (disabled on Windows if no ANSI support) ─────────────────────
def _ansi(code: str) -> str:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleMode(
                ctypes.windll.kernel32.GetStdHandle(-11), 7
            )
        except Exception:
            return ""
    return f"\033[{code}m"

RESET  = _ansi("0")
BOLD   = _ansi("1")
RED    = _ansi("31")
GREEN  = _ansi("32")
YELLOW = _ansi("33")
CYAN   = _ansi("36")
GRAY   = _ansi("90")

# ── Progress bar renderer ─────────────────────────────────────────────────────
_progress_lock = threading.Lock()

def _render_progress(label: str, pct: float, width: int = 28):
    filled = int(width * pct / 100)
    bar    = "█" * filled + "░" * (width - filled)
    line   = f"\r  {CYAN}{bar}{RESET} {YELLOW}{pct:5.1f}%{RESET}  {GRAY}{label}{RESET}"
    with _progress_lock:
        sys.stdout.write(line)
        sys.stdout.flush()

def _clear_progress():
    with _progress_lock:
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()

# ── Argument parser ───────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openrom",
        description=f"{BOLD}OpenROM v2.2{RESET} — Universal ROM Compression Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  openrom --input game.iso --format CHD
  openrom --input game.iso --format CHD --compression High --verify
  openrom --input game.iso --format CHD --output ./converted/
  openrom --folder /roms/ --format CHD --compression Max
  openrom --input game.chd --verify-only
  openrom --list-formats
        """,
    )

    # ── Input source (mutually exclusive) ────────────────────────────────────
    src = parser.add_mutually_exclusive_group()
    src.add_argument(
        "--input", "-i",
        metavar="FILE",
        help="single input ROM file",
    )
    src.add_argument(
        "--folder", "-f",
        metavar="DIR",
        help="convert all supported ROMs in a folder",
    )

    # ── Conversion target ────────────────────────────────────────────────────
    parser.add_argument(
        "--format", "-F",
        metavar="FORMAT",
        help="output format: CHD, CSO, ECM, ISO, BIN, BIN/CUE, XISO",
    )

    # ── Options ──────────────────────────────────────────────────────────────
    parser.add_argument(
        "--output", "-o",
        metavar="DIR",
        help="output directory (default: same as source)",
    )
    parser.add_argument(
        "--compression", "-c",
        choices=["Normal", "High", "Max"],
        default="Normal",
        metavar="LEVEL",
        help="compression level: Normal | High | Max  (default: Normal)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="verify CHD integrity after conversion",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="verify an existing CHD file without converting",
    )
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="print supported conversion formats and exit",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="suppress per-job log output (still prints summary)",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="OpenROM v2.2.0",
    )

    return parser

# ── --list-formats ────────────────────────────────────────────────────────────
def cmd_list_formats():
    print(f"\n{BOLD}Supported conversions:{RESET}\n")
    for src_fmt, targets in CONVERSION_MAP.items():
        targets_str = "  →  " + f"{GRAY},{RESET} ".join(
            f"{CYAN}{t}{RESET}" for t in targets
        )
        print(f"  {BOLD}{src_fmt:<8}{RESET}{targets_str}")
    print()

# ── --verify-only ─────────────────────────────────────────────────────────────
def cmd_verify_only(filepath: str) -> int:
    if not os.path.isfile(filepath):
        print(f"{RED}✗ File not found: {filepath}{RESET}")
        return 2

    info = detect_file(filepath)
    if info.get("format") != "CHD":
        print(f"{RED}✗ --verify-only only works on CHD files.{RESET}")
        return 2

    print(f"\n{BOLD}Verifying:{RESET} {os.path.basename(filepath)}")
    logs = []
    ok = verify_chd(filepath, on_log=lambda m: logs.append(m))
    for line in logs:
        print(f"  {GRAY}{line}{RESET}")

    if ok:
        print(f"\n{GREEN}✅ CHD is valid.{RESET}\n")
        return 0
    else:
        print(f"\n{RED}❌ CHD verification failed.{RESET}\n")
        return 1

# ── Collect jobs from args ────────────────────────────────────────────────────
def collect_jobs(args) -> list[ConversionJob]:
    jobs = []
    target_fmt = args.format.upper() if args.format else None

    def _make_job(filepath: str) -> ConversionJob | None:
        job = ConversionJob(
            filepath=filepath,
            output_dir=args.output or os.path.dirname(os.path.abspath(filepath)),
            target_format="CHD",        # placeholder; resolved below
            compression=args.compression,
            verify=args.verify,
        )
        info = job.get_file_info()

        if "error" in info:
            print(f"{YELLOW}⚠ Skipping {os.path.basename(filepath)}: {info['error']}{RESET}")
            return None

        valid = info.get("valid_targets", [])
        if not valid:
            print(f"{YELLOW}⚠ Skipping {os.path.basename(filepath)}: no valid targets{RESET}")
            return None

        if target_fmt:
            if target_fmt not in valid and target_fmt != "BIN/CUE":
                src_fmt = info.get("format", "?")
                print(
                    f"{YELLOW}⚠ Skipping {os.path.basename(filepath)}: "
                    f"{src_fmt} → {target_fmt} is not supported. "
                    f"Valid: {', '.join(valid)}{RESET}"
                )
                return None
            job.target_format = target_fmt
        else:
            job.target_format = valid[0]

        return job

    if args.input:
        job = _make_job(args.input)
        if job:
            jobs.append(job)

    elif args.folder:
        if not os.path.isdir(args.folder):
            print(f"{RED}✗ Folder not found: {args.folder}{RESET}")
            return []
        detected = detect_folder(args.folder)
        if not detected:
            print(f"{YELLOW}⚠ No supported ROM files found in: {args.folder}{RESET}")
            return []
        for entry in detected:
            job = _make_job(entry["filepath"])
            if job:
                jobs.append(job)

    return jobs

# ── Run batch ─────────────────────────────────────────────────────────────────
def run_batch(jobs: list[ConversionJob], quiet: bool) -> int:
    total   = len(jobs)
    passed  = 0
    failed  = 0

    print(f"\n{BOLD}OpenROM{RESET} — {total} job{'s' if total != 1 else ''} queued\n")

    # Track current job label for the progress renderer
    _current: dict = {"label": ""}

    def on_progress(job: ConversionJob, pct: float):
        _render_progress(_current["label"], pct)

    def on_log(msg: str):
        if not quiet:
            _clear_progress()
            print(f"  {GRAY}{msg}{RESET}")
            # Re-render bar after log line
            if _current["label"]:
                _render_progress(_current["label"], job_ref[0].progress if job_ref else 0)

    job_ref: list = []   # mutable ref so on_log can access current job

    converter = Converter(on_log=on_log, on_progress=on_progress)

    for idx, job in enumerate(jobs):
        label        = f"{os.path.basename(job.filepath)}  →  {job.target_format}"
        _current["label"] = label
        job_ref.clear()
        job_ref.append(job)

        prefix = f"[{idx+1}/{total}]"
        print(f"{BOLD}{prefix}{RESET} {label}")

        ok = converter.convert(job)
        _clear_progress()

        if ok:
            passed += 1
            print(f"  {GREEN}✅ Done{RESET}\n")
        else:
            failed += 1
            err = job.error or "conversion failed"
            print(f"  {RED}❌ Failed — {err}{RESET}\n")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("─" * 48)
    print(f"  {GREEN}✅ Passed: {passed}{RESET}   {RED}❌ Failed: {failed}{RESET}   Total: {total}")
    print("─" * 48 + "\n")

    # Exit codes: 0 = all good, 1 = some failed, 2 = all failed
    if failed == 0:
        return 0
    if passed == 0:
        return 2
    return 1

# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> int:
    parser = build_parser()

    # Print help if no args given
    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()

    # ── Dispatch ──────────────────────────────────────────────────────────────
    if args.list_formats:
        cmd_list_formats()
        return 0

    if args.verify_only:
        if not args.input:
            print(f"{RED}✗ --verify-only requires --input FILE{RESET}")
            return 2
        return cmd_verify_only(args.input)

    if not args.input and not args.folder:
        print(f"{RED}✗ Provide --input FILE or --folder DIR{RESET}")
        parser.print_usage()
        return 2

    if not args.format and not args.verify_only:
        print(f"{YELLOW}⚠ No --format specified — will use first valid target for each file.{RESET}\n")

    # Validate output dir exists if specified
    if args.output and not os.path.isdir(args.output):
        try:
            os.makedirs(args.output, exist_ok=True)
        except Exception as e:
            print(f"{RED}✗ Cannot create output directory: {e}{RESET}")
            return 2

    jobs = collect_jobs(args)
    if not jobs:
        return 2

    return run_batch(jobs, quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())
