#!/usr/bin/env python3
"""
gen_def.py - generate a forwarder .def file for a transparent proxy DLL.

Given the ORIGINAL DLL (or the text output of `dumpbin /exports`), this emits a
module-definition file whose EXPORTS section re-exports every symbol of the
original as a PE forwarder pointing at the renamed original module.

Example of a generated entry:

    EXPORTS
        SomeFunc=Core_orig.SomeFunc @7
        "StdcallFn@8"=Core_orig."StdcallFn@8" @8

Each export is re-exported under its original name AND original ordinal, and
forwarded BY NAME to the renamed original module.  Name-based forwarding is the
only form GNU binutils (MinGW) accepts in a .def, and it is equally valid for
MSVC, so one generated file builds with both toolchains.

Ordinal-only exports
--------------------
Exports that the original publishes with no name (NONAME) cannot be forwarded
by name.  By default they are listed as comments plus a warning.  MSVC can
forward them by ordinal, so pass --ordinal-forward to emit active
`_ord_N=Orig.#N @N NONAME` lines (these build with MSVC's linker but NOT with
MinGW's ld, which rejects the `#ordinal` syntax).

Usage
-----
    # Preferred: read the export table directly (needs: pip install pefile)
    python3 gen_def.py Core.dll -o Core.def

    # Fallback: parse `dumpbin /exports Core.dll > exports.txt` output
    python3 gen_def.py --from-dumpbin exports.txt -o Core.def

Options
-------
    --orig-name NAME   Module the forwarders point at (no .dll, no path).
                       Default: "<stem>_orig" (e.g. Core.dll -> Core_orig).
    --library NAME     Emit a LIBRARY line (usually unnecessary; omitted by
                       default so the linker uses the output file name).
    -o, --output FILE  Write to FILE instead of stdout.
"""
import argparse
import os
import re
import sys


class Export:
    __slots__ = ("ordinal", "name")

    def __init__(self, ordinal, name):
        self.ordinal = ordinal      # int, absolute ordinal
        self.name = name            # str or None (ordinal-only export)


def read_with_pefile(path):
    import pefile  # imported lazily so --from-dumpbin works without it

    pe = pefile.PE(path, fast_load=True)
    pe.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"]]
    )
    if not hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
        raise SystemExit("error: %s has no export table" % path)

    exports = []
    for sym in pe.DIRECTORY_ENTRY_EXPORT.symbols:
        name = sym.name.decode("ascii", "replace") if sym.name else None
        exports.append(Export(int(sym.ordinal), name))
    pe.close()
    return exports


def read_from_dumpbin(path):
    """Best-effort parser for `dumpbin /exports` text output.

    The relevant block looks like:

        ordinal hint RVA      name
              1    0 00011000 SomeFunc
              2    1          SomeData = ...
              3      00011010 [NONAME]

    Column layout varies with dumpbin version, so we parse defensively: a line
    starts an export if its first token is an integer (the ordinal).
    """
    exports = []
    started = False
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            stripped = line.strip()
            if not started:
                # Header row that precedes the table.
                if re.match(r"ordinal\s+hint\s+RVA\s+name", stripped, re.I):
                    started = True
                continue
            if not stripped:
                # A blank line ends the export table.
                if exports:
                    break
                continue
            m = re.match(r"(\d+)\s+(.*)$", stripped)
            if not m:
                # "Summary" section etc.
                if stripped.lower().startswith("summary"):
                    break
                continue
            ordinal = int(m.group(1))
            rest = m.group(2)
            name = _name_from_dumpbin_rest(rest)
            exports.append(Export(ordinal, name))
    if not exports:
        raise SystemExit(
            "error: no exports parsed from %s - is it `dumpbin /exports` "
            "output? (prefer running against the DLL directly with pefile)"
            % path
        )
    return exports


def _name_from_dumpbin_rest(rest):
    toks = rest.split()
    # Drop the hint column if present (a bare integer or hex number).
    if toks and re.fullmatch(r"[0-9a-fA-F]+", toks[0]):
        toks = toks[1:]
    # Drop the RVA column (8 hex digits) if present.
    if toks and re.fullmatch(r"[0-9a-fA-F]{8}", toks[0]):
        toks = toks[1:]
    if not toks:
        return None
    nm = toks[0]
    if nm == "[NONAME]":
        return None
    # Ignore any trailing "= ..." / "(forwarded to ...)" annotations.
    if nm in ("=", "("):
        return None
    return nm


# Characters that are safe to appear unquoted in a .def export name.
_SAFE = re.compile(r"\A[A-Za-z0-9_]+\Z")


def quote(name):
    return name if _SAFE.match(name) else '"%s"' % name


def emit(exports, orig_name, library, ordinal_forward):
    """Return (def_text, noname_ordinals_skipped)."""
    lines = []
    skipped = []
    if library:
        lines.append("LIBRARY %s" % library)
    lines.append("EXPORTS")
    for e in sorted(exports, key=lambda x: x.ordinal):
        if e.name:
            # Forward by name: works on both MinGW (binutils) and MSVC.
            lines.append(
                "    %s=%s.%s @%d"
                % (quote(e.name), orig_name, quote(e.name), e.ordinal)
            )
        elif ordinal_forward:
            # MSVC-only: forward a nameless export by ordinal, hidden by NONAME.
            lines.append(
                "    _ord_%d=%s.#%d @%d NONAME"
                % (e.ordinal, orig_name, e.ordinal, e.ordinal)
            )
        else:
            skipped.append(e.ordinal)
            lines.append(
                "    ; ordinal-only export #%d has no name; not forwardable by "
                "name. Use --ordinal-forward for an MSVC build." % e.ordinal
            )
    lines.append("")
    return "\n".join(lines), skipped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="original DLL, or dumpbin text with --from-dumpbin")
    ap.add_argument("--from-dumpbin", action="store_true",
                    help="treat INPUT as `dumpbin /exports` text, not a DLL")
    ap.add_argument("--orig-name", default=None,
                    help="module the forwarders point at (default: <stem>_orig)")
    ap.add_argument("--library", default=None, help="emit a LIBRARY line")
    ap.add_argument("--ordinal-forward", action="store_true",
                    help="forward nameless (NONAME) exports by ordinal "
                         "(MSVC-only syntax; rejected by MinGW's ld)")
    ap.add_argument("-o", "--output", default=None, help="output .def path")
    args = ap.parse_args(argv)

    if args.orig_name:
        orig_name = args.orig_name
    else:
        stem = os.path.splitext(os.path.basename(args.input))[0]
        if args.from_dumpbin:
            # The input name is a text file, not the DLL; can't derive a stem.
            raise SystemExit("error: --orig-name is required with --from-dumpbin")
        orig_name = stem + "_orig"

    if args.from_dumpbin:
        exports = read_from_dumpbin(args.input)
    else:
        try:
            exports = read_with_pefile(args.input)
        except ImportError:
            raise SystemExit(
                "error: pefile is not installed. Either `pip install pefile` "
                "or run `dumpbin /exports <dll> > exports.txt` and pass "
                "--from-dumpbin exports.txt --orig-name <name>."
            )

    text, skipped = emit(exports, orig_name, args.library, args.ordinal_forward)
    if args.output:
        with open(args.output, "w", encoding="ascii") as fh:
            fh.write(text)
        sys.stderr.write(
            "wrote %d exports to %s (forwarding by name to %s.dll)\n"
            % (len(exports), args.output, orig_name)
        )
    else:
        sys.stdout.write(text)

    if skipped:
        sys.stderr.write(
            "WARNING: %d ordinal-only export(s) were NOT forwarded: %s\n"
            "         Re-run with --ordinal-forward for an MSVC build.\n"
            % (len(skipped), ", ".join("#%d" % o for o in skipped))
        )


if __name__ == "__main__":
    main()
