# Scanner 2.13 large-drive chart patch

Repository: [andresdelcampo/ScannerLargeDrivePatch](https://github.com/andresdelcampo/ScannerLargeDrivePatch)

A small, unofficial patch for Steffen Gerlach's Scanner 2.13 disk-usage
visualizer. It fixes two signed-integer conversions that can distort or hide
large segments of the sunburst chart.

This repository contains the patcher and its tests, **not Scanner itself**.
It is not affiliated with or endorsed by Scanner's original author.

## Apply the patch

You need Python 3.10 or newer and your own copy of the supported Scanner.exe.
The patcher uses only the Python standard library; no packages are required.
The original author's download page is
[Windows Freeware](http://www.steffengerlach.de/freeware/). Availability could
not be confirmed during preparation of this repository.

Close Scanner, then run:

```powershell
python patch_scanner.py --input "C:\Tools\Scanner\Scanner.exe" --output "C:\Tools\Scanner\Scanner-2.13-unofficial1.exe"
```

Run the resulting executable from your existing Scanner folder so it can find
your language file. Its visible version label is
**Version 2.13 (unofficial patch 1)** (the word Version may be localized).
The patcher itself is version **1.0.0**. The author attribution remains intact.

The default output filename is `Scanner-2.13-unofficial1.exe`. Avoid putting
`patch`, `setup`, `install`, or `update` in the executable filename: Windows'
legacy installer detection can request UAC elevation for this unmanifested
32-bit application. The earlier name `Scanner-2.13-unofficial-patch1.exe`
triggered that behavior. Rename an existing copy to the new name; no repatching
is necessary. The visible in-app label can still say "unofficial patch 1".
See [Microsoft's explanation](https://devblogs.microsoft.com/setup/windows-installer-sdk-tools-and-uac-prompts/).

The patcher preserves the input and refuses to overwrite any existing output.
It rejects other executable builds, corrupt inputs, and already-patched files.
To revert, close the patched program and run your original Scanner.exe.
Both executables use the original program's shared settings.

Supported original SHA-256:

```text
ed2231e8f5730ef5adcf80d2c37ab213b92c5bcebbbb1306eba5c6e0bc451620
```

## What this fixes—and the remaining limit

Scanner stores sizes in clusters. Two chart calculations treat unsigned cluster
counts as signed, making large positive sizes negative. With 4 KiB clusters,
the error starts at 8 TiB for a size passed to the chart routine. A small file's
apparent chart placement can also be affected by erroneous parent angles.

The arithmetic correction passed 124 emulated x86 cases and was reported
working by a user on a real 12 TB drive. The supplied before/after screenshots
show a corrected chart, while both display 1.19 TBytes for the selected file
and 10.9 TBytes for the drive total. The screenshots are not included because
they contain personal file paths. The later version-label addition has separate
structural checks; it was not part of that user's runtime comparison.

**This is not unlimited large-drive support.** With 4 KiB clusters, the original
32-bit storage counters still wrap at 16 TiB (approximately 17.6 TB). Other
cluster sizes change both thresholds. See [technical notes](TECHNICAL-NOTES.md).
The patch does not address long paths, Unicode, file permissions, hard-link
accounting, or other unrelated Scanner behavior.

## Developer verification

The tests require the original executable locally; it is never downloaded or
included in the repository. On a compatible 64-bit Python environment:

```powershell
python -m pip install -r requirements-test.txt
python test_scanner_patch.py --input "C:\Tools\Scanner\Scanner.exe"
```

The tests run the actual original and patched machine-code routine in Unicorn,
check the independent expected result, exercise relocated loading, and check
the version string and input rejection. Dependencies are needed only for tests.

## Distribution

Publish the source patcher and documentation only. Scanner's bundled terms
permit redistribution of the package but do not explicitly grant permission
to distribute modified executables. This project does not claim that right.
See [upstream notice](UPSTREAM-NOTICE.md) and [license](LICENSE).

## Credits

Original Scanner 2.13: Steffen Gerlach, copyright 2012.

Unofficial patch project: [andresdelcampo](https://github.com/andresdelcampo).
Made with GPT 6 Astra, with analysis, patch development, and automated
verification assisted by the model and real-drive testing performed by the
project maintainer.
