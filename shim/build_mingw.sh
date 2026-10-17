#!/usr/bin/env bash
#
# build_mingw.sh - build the proxy/shim DLL with MinGW-w64.
#
# Produces, in the output directory, two files you deploy together:
#   <Name>.dll        the shim (drop-in replacement, keeps the original name)
#   <Name>_orig.dll   a copy of the real original the shim forwards to
#
# Usage:
#   ./build_mingw.sh path/to/Original.dll [options]
#
# Options:
#   --arch 32|64   Target architecture. Default: auto-detected from the
#                  original DLL (needs pefile), else 64.
#   --out DIR      Output directory. Default: ./build
#   --name NAME    Base name for the shim (default: original's base name).
#   -h, --help     Show this help.
#
# Requires: x86_64-w64-mingw32-gcc / i686-w64-mingw32-gcc, python3.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

orig_path=""
arch=""
out="./build"
name=""

while [ $# -gt 0 ]; do
  case "$1" in
    --arch) arch="$2"; shift 2 ;;
    --out)  out="$2";  shift 2 ;;
    --name) name="$2"; shift 2 ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
    -*) echo "unknown option: $1" >&2; exit 2 ;;
    *)  orig_path="$1"; shift ;;
  esac
done

if [ -z "$orig_path" ]; then
  echo "error: path to the original DLL is required" >&2
  echo "run: $0 --help" >&2
  exit 2
fi
if [ ! -f "$orig_path" ]; then
  echo "error: no such file: $orig_path" >&2
  exit 2
fi

base="$(basename "$orig_path")"
[ -n "$name" ] || name="${base%.*}"
orig_name="${name}_orig"

# Auto-detect architecture from the original if not forced.
if [ -z "$arch" ]; then
  arch="$(python3 - "$orig_path" <<'PY' 2>/dev/null || true
import sys
try:
    import pefile
    pe = pefile.PE(sys.argv[1], fast_load=True)
    print("32" if hex(pe.FILE_HEADER.Machine) == "0x14c" else "64")
except Exception:
    pass
PY
)"
  [ -n "$arch" ] || arch="64"
  echo "detected arch: $arch-bit"
fi

case "$arch" in
  32) cc="i686-w64-mingw32-gcc" ;;
  64) cc="x86_64-w64-mingw32-gcc" ;;
  *) echo "error: --arch must be 32 or 64" >&2; exit 2 ;;
esac
command -v "$cc" >/dev/null 2>&1 || { echo "error: $cc not found in PATH" >&2; exit 1; }

mkdir -p "$out"
def="$out/${name}.def"
shim_dll="$out/${name}.dll"
orig_dll="$out/${orig_name}.dll"

echo ">> generating export forwarders: $def"
python3 "$here/gen_def.py" "$orig_path" --orig-name "$orig_name" -o "$def"

echo ">> copying original -> $orig_dll"
cp -f "$orig_path" "$orig_dll"

echo ">> compiling shim -> $shim_dll"
"$cc" -O2 -shared \
  -I "$here" \
  -DORIG_DLL_NAME="\"$orig_name\"" \
  -DSHIM_NAME="\"${name}-shim\"" \
  -o "$shim_dll" \
  "$here/shim.c" "$def" \
  -s -static-libgcc

echo ""
echo "done. deploy BOTH files next to the host program:"
echo "    $shim_dll   (rename target: ${name}.dll)"
echo "    $orig_dll"
echo "i.e. replace the original ${name}.dll with the shim, and place"
echo "${orig_name}.dll (the real one) beside it."
