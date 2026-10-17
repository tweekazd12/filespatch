# section_ncg0.bin — deobfuscation analysis

## What it is
Raw **32-bit x86 machine code** (a code section dumped from a binary; starts with the
`55 8B EC` = `push ebp; mov ebp, esp` prologue). 1,613,824 bytes, **no plaintext strings**
(all high-entropy / encrypted).

## The obfuscation ("packing")
Control-flow **jump-threading with junk insertion**:
- Every real instruction is followed by `E9 rel32` (`jmp +N`) that hops over **N bytes of
  random garbage** to the next real instruction.
- Junk is wrapped in flag-preserving noise: `lahf`/`sahf`, `pushfd`, `stc`/`clc`,
  `xor eax, <const>`, and `call $+5; pop` get-EIP thunks.
- ~23,000 such trampolines. Linear disassembly is defeated; **following the jump chain
  recovers the real code**.

## Deobfuscation result
Flow-following disassembler (capstone) that threads unconditional jumps, follows
conditional branches + calls, and drops the trampolines:

| metric | value |
|---|---|
| file size | 1,613,824 bytes |
| **real instructions recovered** | **73,058** |
| real code bytes | 175,004 (**10.8%**) |
| junk bytes | 1,438,820 (**89.2%**) |
| function prologues | 484 |
| call targets | 2,653 |

## Identified routines
- `sub_040506` = **memset** (byte-fill loop, args dst/val/count).
- `sub_059a55` = **memcpy** (called with count 28).
- `sub_0affa7` (and clones) = **get-EIP / position-independent-code thunk**
  (`call $+5; pop eax; add eax,7; ret`).

## Behavior
28 = `sizeof(MEMORY_BASIC_INFORMATION)` (x86). The entry routine copies an MBI and checks:
- `State  == 0x1000`  → **MEM_COMMIT**
- `Type   == 0x40000` → **MEM_MAPPED**
- `Protect== 0x20`    → **PAGE_EXECUTE_READ**

`sub_92` tests whether an address lies within `[BaseAddress, BaseAddress+RegionSize)`.
→ This is a **`VirtualQuery`-driven memory-scanning / self-inspection stub**, the kind of
runtime a packer/protector uses to walk committed, mapped, executable pages
(unpacking / integrity / anti-tamper logic).

## Files
- `section_ncg0.unpacked.asm` — full deobfuscated listing (junk stripped, function
  boundaries marked, `; --- N junk bytes ---` where garbage was removed).
