# ⬡ OpenROM
**Universal ROM Compression Suite** — by M5 Dev

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-cyan)]()

> Convert, compress, and extract ROM files with one click.  
> No terminal. No confusion. Just drop and go.

---

## Supported Formats

| Input | Output | Platform |
|-------|--------|----------|
| ISO, BIN/CUE, GDI, IMG, ECM | CHD | PS1, PS2, Dreamcast, GameCube |
| ISO | CSO | PSP / PS2 |
| BIN / ISO | ECM | PS1 / CD-ROM |
| Xbox ISO | XISO | Original Xbox |
| CHD | ISO / BIN | Any |

---

## Features

- Drag & Drop support
- Batch folder conversion
- Auto ECM decode before conversion
- Auto CUE generation for lone BIN files
- CHD verification after conversion
- Portable + Installer editions
- Dark theme, Ko-fi donate button

---

## Tools Bundled

- [chdman](https://www.mamedev.org/) — MAME CHD tool
- [maxcso](https://github.com/unknownbrackets/maxcso) — PSP CSO compression
- [ecm/unecm](https://github.com/37712/ECM-Tools) — ECM encode/decode
- [extract-xiso](https://github.com/XboxDev/extract-xiso) — Xbox XISO tool

---

## Installation

### Portable
Download `OpenROM-portable.zip`, extract, run `OpenROM.exe`

### Installer
Download `OpenROM-setup.exe`, follow wizard

---

## Build from Source

```bash
git clone https://github.com/M5Devs/OpenROM
cd OpenROM
pip install -r requirements.txt
python main.py
```

To build .exe:
```bash
build.bat
```

---

## License

GPL v3 — See [LICENSE](LICENSE)

---

## Support



Made with ❤️ by [M5 Dev](https://github.com/M5Devs) —
