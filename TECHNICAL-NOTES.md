# Technical notes

## Cause and correction

The supported executable is native x86 Borland Delphi code. File/folder sizes
are stored as unsigned 32-bit cluster counts. The chart-angle routine at virtual
address 0x449298 contains two signed x87 loads of an unsigned count:

```text
mov [esp+4], ecx
fild dword [esp+4]
```

At 2^31 clusters the resulting floating-point size becomes negative. Replace
both conversions with calls to a helper that first zero-extends the value:

```text
push 0
push ecx
fild qword [esp]
add esp, 8
ret
```

This preserves general registers and stack balance, and produces one x87
result like the replaced instructions. No consumer relies on the original
temporary stack slot after the conversion. The following arithmetic overwrites
or does not depend on the helper's changed integer flags.

## Exact supported image and edits

Original SHA-256:
`ed2231e8f5730ef5adcf80d2c37ab213b92c5bcebbbb1306eba5c6e0bc451620`

Patcher 1.0.0 output SHA-256:
`b9a3d2ad26453a7c8e3a2d68fdfe735a1e0762849229f2ea85296c01941e878a`

Output filename: `Scanner-2.13-unofficial1.exe`. This replaces the initial
`Scanner-2.13-unofficial-patch1.exe` filename. The rename changes no bytes, so
the output hash and arithmetic validation remain valid.

## UAC and the executable filename

The original and both patched builds have no embedded application manifest.
No Scanner-specific RunAsAdmin entry was found in the checked per-user or
machine-wide AppCompat Layers registry settings. The patch adds no request
for elevated privileges.

Windows' legacy installer detection can infer an installer from "patch" in a
32-bit executable's filename when it lacks an execution-level manifest.
The initial labeled filename triggered a UAC prompt; the maintainer confirmed
the renamed copy was satisfactory. The default filename now avoids that
keyword, while the in-app version label retains the unofficial patch identity.
[Microsoft documents this behavior](https://devblogs.microsoft.com/setup/windows-installer-sdk-tools-and-uac-prompts/).

## Binary layout

Addresses use the original image base 0x400000.

| Location | Change |
| --- | --- |
| VA 0x4492B3 / file 0x486B3 | Eight-byte conversion replaced with relative call and three NOPs |
| VA 0x449314 / file 0x48714 | Same change in the second chart path |
| VA 0x44F370 / file 0x4E770 | Ten-byte helper in previously zero-filled CODE padding |
| VA 0x44F380 / file 0x4E780 | Delphi string header, unofficial version text, and terminator in CODE padding |
| VA 0x448790 / file 0x47B90 | Existing version-string pointer redirected to VA 0x44F388 |
| File 0x200 | CODE virtual size extended to include the added string |

The version text is ` 2.13 (unofficial patch 1)`; the existing UI supplies the
localized Version prefix. Its Delphi AnsiString header contains reference count
-1 and the ASCII byte length. The original pointer's relocation entry is
preserved. No imports, sections, resources, or relocation entries are added.
The original author attribution, entry point, and file length remain intact.
The original PE checksum is zero and remains zero.

The initial arithmetic-only test build changed 26 bytes and had SHA-256
`7cf1c1dc96b13c712bc39602cd216274b39ecbd24905eb559dee0600dbcf3d16`.
The user confirmed that build on a real 12 TB drive. The labeled output adds
identification but uses exactly the same arithmetic correction.

## Remaining capacity boundaries

| Cluster size | Signed-chart error starts | Unsigned counter wrap boundary |
| --- | --- | --- |
| 512 bytes | 1 TiB | 2 TiB |
| 1 KiB | 2 TiB | 4 TiB |
| 4 KiB | 8 TiB | 16 TiB |
| 64 KiB | 128 TiB | 256 TiB |

The patch removes the middle-column error only. The last column is an exclusive
arithmetic boundary, not certification of all filesystems below that size.
Widening the stored counts requires broader changes to structures and consumers.

The drive query uses GetDiskFreeSpaceA cluster outputs for operational counts.
GetDiskFreeSpaceExA is also called, but its 64-bit results in that routine feed
diagnostic logging. Microsoft documents the cluster outputs in
[GetDiskFreeSpaceA](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getdiskfreespacea).

## Validation

The test suite executes the original and patched x86 function with Unicorn.
It covers both focused and summary paths, four cluster sizes, counts around
2^31 and up to 2^32-1, zero cases, and normal and relocated loading: 124 cases.
Below 2^31 the floating-point outputs match the original exactly. Above that
boundary the correction agrees with independently calculated expected angles.
It checks returned stack balance and preservation of EBX.

A fixed 12 TB example uses 2,929,716,735 total clusters, 450,182,102 free
clusters, and 4,096 bytes per cluster. For its used count:

| Case | Original radians | Patched radians |
| --- | ---: | ---: |
| Used segment, one-drive summary | -3.893448 | 5.317707 |
| Entire focused root | -4.600339 | 6.283185 |

Additional checks validate the unofficial string, its Delphi header, its
relocation entry and relocated pointer, and rejection of invalid/already-patched
inputs. Real-drive success is user-reported for the arithmetic-only build;
the newly labeled build has structural checks but no recorded visual verification.
