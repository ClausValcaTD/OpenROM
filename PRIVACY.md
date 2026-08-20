# Privacy Policy

**OpenROM** — M5 Dev
Last updated: 2026-08-20

---

## 1. Overview

OpenROM is a local desktop application. It does not connect to the internet, does not collect personal data, and does not transmit anything to any server.

---

## 2. Data We Do NOT Collect

- No personal information
- No usage analytics or telemetry
- No crash reports sent externally
- No ROM file contents, names, or metadata uploaded anywhere
- No IP addresses or device identifiers

---

## 3. Data Stored Locally on Your Device

OpenROM stores the following files **only on your own machine**:

| What | Where | Why |
|------|-------|-----|
| Application settings | OS config directory | Save your preferences |
| Conversion logs | OS config directory `/logs/` | Debug and audit trail |

**OS config directory locations:**
- Windows: `%APPDATA%\OpenROM\`
- macOS: `~/Library/Application Support/OpenROM/`
- Linux: `~/.config/OpenROM/`

You can delete these files at any time. The app will regenerate defaults on next launch.

---

## 4. Your ROM Files

OpenROM processes your ROM files **entirely on your local machine**.

- Files are never uploaded, scanned externally, or shared
- Temporary files created during conversion are deleted automatically after each job
- Output files are written only to the directory you specify

---

## 5. Internet Access

OpenROM does **not** make any network requests. There is no:

- Update checker
- License verification server
- Analytics endpoint
- Cloud sync

If a future version adds any network feature, this policy will be updated and clearly communicated in the release notes before the update ships.

---

## 6. Third-Party Tools

OpenROM bundles the following open-source binaries to perform conversions:

- `chdman` (MAME project — BSD License)
- `maxcso` (unknownbrackets — ISC License)
- `ecm` / `unecm` (Neill Corlett)
- `extract-xiso` (in0finite)

These tools run locally on your machine. They do not connect to the internet or collect data.

---

## 7. Children's Privacy

OpenROM does not collect any data from anyone, including minors.

---

## 8. Changes to This Policy

If this policy changes, the updated version will be committed to the repository with a clear note in the release changelog. Continued use of the app after an update constitutes acceptance of the revised policy.

---

## 9. Contact

For privacy-related questions:
**GitHub:** https://github.com/M5Devs/OpenROM/issues
