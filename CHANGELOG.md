# Changelog

## 1.0.0 — 2026-09-11

- Fix unsigned cluster-to-angle conversion in both chart paths of the supported
  Scanner 2.13 executable.
- Identify generated programs as 2.13 (unofficial patch 1), retaining upstream
  attribution. This is not an official Scanner version bump.
- Name generated executables `Scanner-2.13-unofficial1.exe`. The initial name
  `Scanner-2.13-unofficial-patch1.exe` triggered Windows' legacy UAC installer
  detection because it contained "patch". Renaming existing copies is enough;
  executable contents, in-app version label, and output SHA-256 are unchanged.
- Preserve the original file and require an exact SHA-256 input match.
- Include 124 arithmetic regression cases and additional label, relocation,
  and invalid-input checks.
- Record user confirmation on a 12 TB drive; document the remaining 16 TiB
  counter boundary for 4 KiB clusters.
- Prepare source-only distribution with a scoped MIT license.
- Document the repository at https://github.com/andresdelcampo/ScannerLargeDrivePatch
  and credit development assistance from GPT 6 Astra.
- Include a maintainer-supplied screenshot of the corrected chart and visible
  unofficial version label, without personal file paths.
