import os
import json
import platform

CONFIG_FILE = "config.json"

def get_default_bundled_path(tool: str) -> str:
    system = platform.system()
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if tool == "chdman":
        if system == "Windows":
            return os.path.join(base, "assets", "windows", "chdman.exe")
        elif system == "Linux":
            bundled = os.path.join(base, "assets", "linux", "chdman")
            return bundled if os.path.isfile(bundled) else "chdman"
        return "chdman"

    names = {
        "Windows": {
            "ecm":    "ecm.exe",
            "unecm":  "unecm.exe",
            "maxcso": "maxcso.exe",
            "xiso":   "extract-xiso.exe",
        },
        "Linux": {
            "ecm":    "ecm",
            "unecm":  "unecm",
            "maxcso": "maxcso",
            "xiso":   "extract-xiso",
        },
    }
    folder = "windows" if system == "Windows" else "linux"
    fname  = names.get(system, names["Linux"]).get(tool, tool)
    bundled = os.path.join(base, "assets", folder, fname)
    return bundled if os.path.isfile(bundled) else tool

DEFAULT_CONFIG = {
    "chdman": "",
    "maxcso": "",
    "ecm": "",
    "unecm": "",
    "xiso": ""
}

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Ensure all keys are present
                for k in DEFAULT_CONFIG:
                    if k not in config:
                        config[k] = ""
                return config
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass

def get_tool_path(tool: str) -> str:
    config = load_config()
    val = config.get(tool, "")
    if val and (os.path.exists(val) or os.path.isabs(val)):
        return val
    # Fallback to defaults
    return get_default_bundled_path(tool)
