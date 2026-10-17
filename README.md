# filespatch

Tooling for building a **transparent proxy / shim DLL** — a drop-in replacement
that re-exports every symbol of an original DLL, forwards each to the renamed
original via the PE export-forwarder mechanism, and runs your own code at load
time (for logging, inspection, configuration, or hooks).

See [`shim/README.md`](shim/README.md) for the full build and deployment guide.

## Quick start (MinGW)

```sh
cd shim
./build_mingw.sh path/to/Core.dll     # -> build/Core.dll + build/Core_orig.dll
```

Then deploy both files next to the host program: rename the real `Core.dll` to
`Core_orig.dll` and drop the shim in as `Core.dll`.
