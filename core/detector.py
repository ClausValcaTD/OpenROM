import os
import platform


SUPPORTED_INPUT = {
    ".iso": "ISO",
    ".bin": "BIN",
    ".cue": "CUE",
    ".gdi": "GDI",
    ".img": "IMG",
    ".ecm": "ECM",
    ".chd": "CHD",
    ".cso": "CSO",
    ".zso": "ZSO",
}

PLATFORM_MAP = {
    "ISO":  "Unknown",
    "BIN":  "CD-ROM",
    "CUE":  "CD-ROM",
    "GDI":  "Dreamcast",
    "IMG":  "CD-ROM",
    "ECM":  "CD-ROM",
    "CHD":  "CHD Archive",
    "CSO":  "PSP/PS2",
    "ZSO":  "PSP/PS2",
}

# ── Valid conversion map ──────────────────────────────────────────────────────
# Key: source format → list of valid target formats
CONVERSION_MAP = {
    # Source  : valid output formats
    "ISO":  ["CHD", "CSO", "ECM", "XISO"],  # CHD=createdvd, CSO=maxcso, ECM=ecm, XISO=two-step extract-xiso
    "BIN":  ["CHD", "ECM"],                  # CHD=createcd (+auto-CUE), ECM=ecm
    "CUE":  ["CHD"],                         # CHD=createcd (BIN+CUE pair)
    "GDI":  ["CHD"],                         # CHD=createcd
    "IMG":  ["CHD"],                         # CHD=createdvd
    "ECM":  ["ISO"],                         # unecm → raw BIN/ISO
    "CHD":  ["ISO", "BIN"],                  # extractdvd→ISO  or  extractcd→BIN+CUE
    "CSO":  ["ISO"],                         # maxcso --decompress
    "ZSO":  ["ISO"],                         # maxcso --decompress (ZSO supported)
    "XISO": ["ISO"],                         # extract-xiso -r (rewrite/strip padding)
}


def get_valid_targets(fmt: str) -> list:
    """Return valid output formats for a given source format."""
    return CONVERSION_MAP.get(fmt.upper(), [])


def detect_file(filepath: str) -> dict:
    """
    Returns dict with:
      - format: str
      - platform: str
      - size_bytes: int
      - size_str: str
      - needs_ecm_decode: bool
      - paired_cue: str | None  (for BIN files)
      - paired_bin: str | None  (for CUE files)
      - chd_type: str | None    ('cd' or 'dvd', detected by size for CHD)
      - valid_targets: list[str]
    """
    if not os.path.isfile(filepath):
        return {"error": f"File not found: {filepath}"}

    name = os.path.basename(filepath).lower()
    ext  = os.path.splitext(name)[1]
    size = os.path.getsize(filepath)

    # ECM check — e.g. game.bin.ecm
    needs_ecm = False
    real_ext  = ext
    if ext == ".ecm":
        needs_ecm = True
        inner = os.path.splitext(os.path.splitext(name)[0])[1]
        real_ext = inner if inner else ".ecm"

    fmt  = SUPPORTED_INPUT.get(real_ext, "UNKNOWN")
    plat = _guess_platform(filepath, fmt, size)

    # For CHD: guess if it's CD or DVD based on nothing (we don't know until
    # chdman info runs), so we store None and let converter call chdman info.
    chd_type = None
    if fmt == "CHD":
        chd_type = _guess_chd_type(size)

    result = {
        "format":           fmt,
        "platform":         plat,
        "size_bytes":       size,
        "size_str":         _human_size(size),
        "needs_ecm_decode": needs_ecm,
        "paired_cue":       None,
        "paired_bin":       None,
        "chd_type":         chd_type,
        "valid_targets":    get_valid_targets(fmt),
    }

    # BIN → look for matching CUE
    if fmt == "BIN":
        cue = _find_pair(filepath, ".cue")
        result["paired_cue"] = cue

    # CUE → look for matching BIN
    if fmt == "CUE":
        bn = _find_pair(filepath, ".bin")
        result["paired_bin"] = bn

    return result


def detect_folder(folder: str) -> list:
    """Scan folder and return list of detected files (non-recursive)."""
    results = []
    if not os.path.isdir(folder):
        return results
    for fname in os.listdir(folder):
        fpath = os.path.join(folder, fname)
        if not os.path.isfile(fpath):
            continue
        ext = os.path.splitext(fname.lower())[1]
        if ext in SUPPORTED_INPUT:
            info = detect_file(fpath)
            info["filepath"] = fpath
            info["filename"] = fname
            results.append(info)
    return results


from core.config import get_tool_path as _get_tool_path

def get_chdman_path() -> str:
    return _get_tool_path("chdman")


def get_tool_path(tool: str) -> str:
    """
    tool: 'ecm' | 'unecm' | 'maxcso' | 'xiso'
    Returns path to configured or bundled binary, falling back to system PATH.
    """
    return _get_tool_path(tool)


# ── helpers ──────────────────────────────────────────────────────────────────

def _guess_platform(filepath: str, fmt: str, size: int) -> str:
    if fmt == "GDI":
        return "Dreamcast"
    if fmt in ("CSO", "ZSO"):
        return "PSP/PS2"
    if fmt in ("ISO", "BIN", "IMG"):
        mb = size / (1024 * 1024)
        if mb < 800:
            return "PS1"
        elif mb < 2000:
            return "PS2 / GC"
        else:
            return "PS2 / Wii"
    return PLATFORM_MAP.get(fmt, "Unknown")


def _guess_chd_type(size: int) -> str:
    """Rough heuristic — CD images are usually < 900 MB."""
    mb = size / (1024 * 1024)
    return "cd" if mb < 900 else "dvd"


def _find_pair(filepath: str, target_ext: str) -> str | None:
    base = os.path.splitext(filepath)[0]
    candidate = base + target_ext
    return candidate if os.path.isfile(candidate) else None


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
