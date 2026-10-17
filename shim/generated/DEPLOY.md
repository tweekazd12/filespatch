# Prebuilt shim for this target (`Core.dll`, L2 JP D10 client)

`Core.def` here is the forwarder table generated from the triage `report.txt`:
**3,314 exports, forwarded by name to `Core_orig`, ordinals 1–3314 preserved.**
The target is **PE32 / x86 (I386)**, so build the shim **32-bit**.

## Build

You do **not** need the real `Core.dll` to *build* the shim — PE forwarders are
resolved at runtime, so the generated `.def` is enough:

```sh
# MinGW (Linux or Windows), from the repo root:
i686-w64-mingw32-gcc -O2 -shared -I shim \
  -DORIG_DLL_NAME="\"Core_orig\"" -DSHIM_NAME="\"Core-shim\"" \
  -o Core.dll shim/shim.c shim/generated/Core.def -s -static-libgcc
```

or regenerate + build in one step straight from your real DLL:

```sh
./shim/build_mingw.sh path/to/Core.dll --arch 32
```

## Deploy (runtime)

Put both files where the host loads `Core.dll` from:

1. Rename the real `Core.dll` → `Core_orig.dll`.
2. Drop the built shim in as `Core.dll`.

On load you get a `Core-shim.log` next to the DLL; every call is forwarded to
`Core_orig.dll`.

## Important: this target's realities

These are factual constraints of *this* binary (from the triage), not steps to
work around anything:

- **It is Authenticode-signed.** The shim is not, so replacing `Core.dll` with
  it breaks that signature. If the launcher/host verifies `Core.dll`'s
  signature or integrity, it will reject an unsigned replacement.
- **It is packed by a custom protector** (`.ncg0–.ncg6`) and the triage reports
  **anti-tamper / integrity, HWID, and watchdog** subsystems. All of that still
  runs inside `Core_orig.dll` when forwarded. A protector that checks its own
  module name/path/base, or that something is proxying it, may refuse to run.

So this shim is a correct, complete *interop/forwarding* layer. Whether it
*loads* in a given host depends on that host's integrity/signature checks,
which this project does not touch.

## Intercepting a specific function

To hook one export instead of forwarding it: delete its line from `Core.def`,
implement a function of the same (demangled) signature in `shim.c`, and call
the real one via `Shim_GetOriginal()` + `GetProcAddress`. Everything else keeps
forwarding unchanged.
