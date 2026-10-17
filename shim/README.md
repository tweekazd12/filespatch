# Transparent proxy / shim DLL

A drop-in replacement DLL that **re-exports every symbol of an original DLL and
forwards each one to the renamed original**, while running your own code at
load time. Use it to log, inspect, configure, or hook a library without
touching the host program.

```
host.exe  --imports-->  Core.dll (shim)  --PE forwarders-->  Core_orig.dll (real)
                              |
                              +-- DllMain -> Shim_OnAttach()  (your code)
```

The forwarding is done by the PE **export-forwarder** mechanism: the shim's
export table entry for each symbol holds the string `Core_orig.<Name>` instead
of a code address, and the Windows loader transparently redirects every import
to the real DLL. This is correct for every calling convention, for data
exports, and costs nothing at call time — no per-function thunks, no
reimplementation of the API.

## Files

| File             | Purpose                                                        |
|------------------|----------------------------------------------------------------|
| `shim.c`         | `DllMain` + lifecycle hooks (`Shim_OnAttach`/`Shim_OnDetach`). |
| `shim.h`         | Declarations for the shim's own code.                          |
| `config.h`       | Compile-time config (original module name, logging).           |
| `gen_def.py`     | Reads the original's exports and writes the forwarder `.def`.  |
| `build_mingw.sh` | One-shot build with MinGW-w64 (Linux or Windows).              |
| `build_msvc.bat` | One-shot build with MSVC (VS Native Tools prompt).             |

## Prerequisites

- **Python 3** with [`pefile`](https://pypi.org/project/pefile/):
  `pip install pefile` (only needed to read the exports; see the dumpbin
  fallback below if you can't install it).
- A compiler:
  - **MinGW-w64** — `x86_64-w64-mingw32-gcc` and/or `i686-w64-mingw32-gcc`
    (works cross-platform; the recommended path), **or**
  - **MSVC** — `cl` / `link` from a Visual Studio "Native Tools" prompt.

## Build (MinGW, recommended)

```sh
./build_mingw.sh path/to/Core.dll
#   --arch 32|64   force architecture (default: auto-detected from the DLL)
#   --out  DIR     output directory (default: ./build)
#   --name NAME    shim base name (default: the original's base name)
```

This writes to `./build`:

- `Core.dll` — the shim (deploy this under the original's name),
- `Core_orig.dll` — a copy of the real original, which the shim forwards to.

## Build (MSVC)

From an **x64** (or **x86**) *Native Tools Command Prompt for VS*, with
`python` on `PATH`:

```bat
build_msvc.bat path\to\Core.dll
```

The MSVC build passes `--ordinal-forward`, so ordinal-only exports are proxied
too (see the caveat below).

## Deploy

Put both files in the host program's directory (or wherever it loads the DLL
from):

1. Rename/replace the real `Core.dll` so it becomes `Core_orig.dll`.
2. Drop the freshly built shim in as `Core.dll`.

The loader now loads your shim as `Core.dll`; every imported symbol is
forwarded to `Core_orig.dll`. If logging is enabled (default) a `Core-shim.log`
appears next to the DLL on first load.

> **Keep the arch matched.** A 32-bit host needs a 32-bit shim and 32-bit
> original; likewise for 64-bit. `build_mingw.sh` auto-detects from the
> original.

## Adding your own behavior

Edit `shim.c`:

- `Shim_OnAttach()` runs once when the DLL is loaded. Install hooks, read
  config, start logging here. Return `FALSE` to abort the load.
- `Shim_OnDetach()` runs at unload for cleanup.
- `Shim_GetOriginal()` lazily `LoadLibrary`s the original so you can call into
  it with `GetProcAddress`, e.g. to wrap a specific function.
- `Shim_Log(fmt, ...)` appends a timestamped line to the log file.

To *intercept* a specific export (rather than just forward it), remove that one
symbol from the generated `.def`, implement a real function of the same name in
`shim.c` that does your work and then calls through to the original via
`Shim_GetOriginal()` + `GetProcAddress`. Everything else keeps forwarding
untouched.

## Generating the `.def` by hand

`build_*` call `gen_def.py` for you, but you can run it directly:

```sh
python3 gen_def.py Core.dll --orig-name Core_orig -o Core.def
```

No `pefile`? Use the dumpbin fallback:

```bat
dumpbin /exports Core.dll > exports.txt
python3 gen_def.py --from-dumpbin exports.txt --orig-name Core_orig -o Core.def
```

Already have a triage `report.txt` (lines `ord N rva 0x.. NAME`)? Build the
`.def` straight from it, no DLL or `pefile` needed:

```sh
python3 gen_def.py report.txt --from-report --orig-name Core_orig -o Core.def
```

## Caveats & toolchain differences

- **Ordinal-only (NONAME) exports.** Symbols the original exports with *no
  name* can't be forwarded by name. MSVC can forward them by ordinal
  (`--ordinal-forward`, used automatically by `build_msvc.bat`); MinGW's `ld`
  rejects the `#ordinal` syntax, so the MinGW build lists them as comments and
  prints a warning. Most DLLs (including UE2-era game modules) export by name,
  so this rarely matters — but check the warning. If you must proxy a
  nameless ordinal on MinGW, intercept it with a hand-written thunk instead.
- **Decorated names.** x86 `stdcall` (`Name@N`) and C++ mangled names are
  copied verbatim from the export table and quoted in the `.def`; both
  toolchains accept them.
- **Ordinals are preserved.** Each export keeps the original's ordinal, so
  clients that import by ordinal still resolve.

## A note on intended use

This is a standard, dual-use systems technique (compatibility shims, logging,
instrumentation, modding). Use it only on software you own or are authorized to
modify, and in line with that software's license and terms.
