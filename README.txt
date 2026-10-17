Game/engine instruction stream pulled from Core.dll (ncg0)
==========================================================

WHAT THIS IS
  ncg0_game_instructions.asm  - the actual game/engine x86 instructions,
                                with the protector's noise instructions removed.
  ncg0_full_unpacked.asm      - the earlier full listing (junk-jumps removed only),
                                kept for comparison.

HOW IT WAS PRODUCED (static only - nothing decrypted or bypassed)
  Starting from the jump-threaded recovery of ncg0, a peephole pass removed the
  obfuscator's semantic-NOP "noise":
    - flag save/restore ...... lahf, sahf, pushfd, popfd, pushf, popf
    - flag dirtying .......... stc, clc, cmc, std, cld
    - padding ................ nop
    - opaque predicates ...... `cmp X,X` self-compares; the conditional jump that
                               follows is annotated ALWAYS TAKEN / dead.

NUMBERS
  73,058 recovered instructions
   9,168 (12.5%) protector noise  -> removed
  63,890 (87.5%) game/engine instructions -> kept
     456 opaque conditional branches resolved/annotated

LIMITS (read before trusting a given address)
  1. Strings and the import table are still RUNTIME-ENCRYPTED. They were NOT
     decrypted or rebuilt - this is only the instruction stream.
  2. ncg0 interleaves high-entropy ENCRYPTED DATA POOLS between code. Those bytes
     can disassemble as bogus instructions (tell-tale: runs of int1/aas/xchg/les/
     in/out and nonsensical operands). Treat such runs as data, not code.
  3. Control flow that goes through indirect/register jumps is not fully threaded.

So: this is a faithful, denoised view of the *reachable game instructions*, useful
for reading the logic - not a recompilable or fully-resolved dump.
