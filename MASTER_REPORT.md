# Core.dll — Static PE Triage Report

**Scope:** static, non-circumventing inspection only. Nothing was unpacked, decrypted,
or executed. Packed regions are reported by their raw bytes / entropy, not decoded.

## 1. Identity

| Field | Value |
|---|---|
| File | `aff5143f-Core.dll` |
| Size | 1,944,864 bytes |
| Type | PE32 DLL, Intel x86 (I386), GUI subsystem |
| MD5 | `fe45b3caf0e68100d59680b0795eb077` |
| SHA1 | `05f574378464cc5b52943ab2fd5ef97de247880a` |
| SHA256 | `79f8ded264a3532f6f3cac7a67a830a275ad1cbea234bc53e752b6da3b00de4b` |
| TimeDateStamp | `0x6ABCCFB3` → 2026-09-30 09:00:35 UTC |
| ImageBase | `0x10000000` |
| EntryPoint RVA | `0x000B0A02` (inside `.ncg0`) |
| DllCharacteristics | ASLR (DYNAMIC_BASE) + DEP (NX_COMPAT) |
| Overall entropy | 7.31 |

**What it is:** a **Lineage 2 game client `Core.dll`**, built on an Unreal-Engine-2-era
codebase (class prefixes `U*`/`F*`/`T*`, `UObject`, `FArchive`, `UExporter`, `.u` packages).
Leaked PDB path gives the build provenance:

```
D:\Work\JP_D10_260826_Patch\Client\Core\Lib\Core.pdb
```

i.e. a **Japanese ("JP") client, "D10" patch**, build string `260826` (26-08-26 → 2026-08-26).
CodeView GUID: `56F2DA2C-8540-4FFE-B7B3-968C7D06F537`, age 1.

## 2. Protection / packing assessment

The binary is wrapped by a **custom protector** whose sections are renamed `.ncg0`–`.ncg6`
("ncg" is not a known off-the-shelf protector such as Themida/VMProtect/Enigma — it looks
in-house/private). Evidence it is packed rather than a plain build:

- **Import table is gutted:** the only classic import is `USER32.DLL!MessageBoxW`. A 1.9 MB
  Unreal module cannot really run on one import — the real imports are resolved at runtime
  by the loader stub (typical of a packer/protector).
- **`.ncg0` is RWX-ish code** (R/X/code) at **entropy 7.67** over 1.6 MB — consistent with
  encrypted/compressed code that is unpacked in memory at load. The entry point lives here.
- Original section names (`.text`, `.text$di`) and the GuardCF load-config table survive as
  remnants inside `.ncg4`, showing the original MSVC layout before wrapping.

So: statically you get the **export table, resources, debug record, and whatever strings sit
in the low-entropy data section**. The actual code bodies in `.ncg0` are not readable without
running/unpacking it, which I did not do.

## 3. Sections (`.ncg0`–`.ncg6`)

| Name | VirtAddr | VirtSize | RawSize | Entropy | Flags | Interpretation |
|---|---|---|---|---|---|---|
| `.ncg0` | 0x1000 | 0x5AAE0C | 0x18A000 | 7.67 | R X Code | Packed/encrypted code body + entrypoint |
| `.ncg1` | 0x5AC000 | 0x1000 | 0 | 0.00 | R Init | Virtual-only (uninit; unpack scratch/BSS) |
| `.ncg2` | 0x5AD000 | 0x49C06 | 0x49E00 | 3.84 | R Init | Data — holds the readable strings & export name table |
| `.ncg3` | 0x5F7000 | 0x2000 | 0x2000 | 3.65 | R W Init | IAT / thunks (`USER32.DLL`, `MessageBoxW` visible) |
| `.ncg4` | 0x5F9000 | 0x1000 | 0x800 | 2.64 | R Init | Debug dir: RSDS/PDB record + leaked COFF group names |
| `.ncg5` | 0x5FA000 | 0x1E0 | 0x200 | 4.72 | R Init | Resources: app manifest (trustInfo) + version block |
| `.ncg6` | 0x5FB000 | 0x1000 | 0x400 | 0.17 | R Init | Load-config / reloc stub (mostly zero) |

Each section's raw bytes were carved to `section_ncg0.bin` … `section_ncg6.bin`.

## 4. Exports

**3,314 exported symbols**, all MSVC-mangled and fully demangled. Full list:
`exports_mangled.txt` (raw) and `exports_demangled.txt` (readable). Grouped by class
(`export_class_summary.txt`), top owners:

| Count | Class |
|---|---|
| 713 | free / global functions & variables |
| 523 | `UObject` |
| 83 | `FString` |
| 77 | `L2UserHardWareInformation` |
| 68 | `L2Configuration` |
| 46 | `FArchive` |
| 39 | `FConfigCacheIni` |
| 34 | `UStruct` |
| 32 | `FName` |
| 31 | `UClass` |

103 distinct classes in all. Notable subsystems surfaced by the exports:

- **Crypto / codecs:** `FBlowFish` (`BlowfishEncrypt`/`BlowfishDecrypt`/`Blowfish_encipher`/
  `Blowfish_decipher`), `FL2RSACodec` (`Encode`/`Decode`), `FCrc` (CRC tables),
  global codec pointers `GL2DESCodec`, `GL2CurrentTxtCodec` — these are the L2
  packet/package encryption primitives.
- **Hardware fingerprinting:** `L2UserHardWareInformation` (77 members) — HWID collection.
- **Config:** `L2Configuration`, `FConfigCacheIni`, `FConfigFile`, `FParamMap`.
- **Threading / watchdog:** `L2ThreadUtil`, `L2ThreadBase`, `L2HangDetectMarker`.
- **Engine core:** `UObject`/`UClass`/`UStruct`/`UProperty` family, `FArchive`,
  `ULinkerLoad`, `UPackage`/`UPackageMap`, `FBitReader`/`FBitWriter`,
  shader globals (`GL2ShaderPath`, `GL2ShaderWater`, etc.), `GIsL2SuperShadow`.

## 5. Strings

- **17,144 ASCII strings** with file offsets → `strings_ascii.txt`
- **UTF-16LE strings** → `strings_utf16.txt` (sparse; the readable data lives in `.ncg2`)

Most runtime format strings are mangled (`%S…` fragments) because they sit inside the
packed `.ncg0` region; clean strings come from `.ncg2` (export names) and the resource/debug
sections. High-signal items:

- PDB path (above).
- Microsoft Authenticode / code-signing + timestamp CA URLs in the cert blob
  (`oneocsp.microsoft.com`, `www.microsoft.com/pkiops/...`) — the DLL is **Authenticode-signed**.
- App manifest requesting standard trust (from `.ncg5`).

## 6. Deliverable files

All in the scratchpad directory:

- `MASTER_REPORT.md` — this file
- `report.txt` — raw headers/sections/imports/exports dump
- `exports_mangled.txt` / `exports_demangled.txt` — all 3,314 symbols
- `export_class_summary.txt` — class → export count
- `strings_ascii.txt` / `strings_utf16.txt` — all strings with offsets
- `section_ncg0.bin` … `section_ncg6.bin` — carved section bytes

## 7. What static triage cannot give you here

The bodies of the functions in `.ncg0` are packed; a flat disassembly of that section yields
garbage until the protector's stub decrypts it in memory. Getting real disassembly means
running/unpacking the protector, which is the circumvention step I'm not doing. If you own
this and want the code, the supported route is the original build artifacts / the `Core.pdb`
named in the debug record, not the shipped binary.
