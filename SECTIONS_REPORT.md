# Dumped PE sections (ncg0–ncg5) — consolidated analysis

All six `*-section_ncgN.bin` files are **sections dumped from one 32-bit PE** — an
**obfuscated/protected `Core.dll`** (image base `0x10000000`, the default DLL base).

## Origin (from the debug record in ncg4)
```
PDB  : D:\Work\JP_D10_260826_Patch\Client\Core\Lib\Core.pdb
GUID : 2CDAF256-4085-4FFE-B7B3-968C7D06F537
Age  : 1
```
→ Original module **`Core.dll`**, built from a `Client\Core` tree inside a dated
regional patch (`JP_D10_260826_Patch`). The build layout (`Client`, `Core`, "Patch")
plus the heavy code obfuscation is consistent with a **game-client core library under a
commercial protector / anti-tamper**.

## Section-by-section

| section | size | role | evidence |
|---|---|---|---|
| **ncg0** | 1.6 MB | **`.text` — obfuscated code** | 32-bit x86, jump-threaded + 89% junk; `VirtualQuery` memory-scan stub (see prior report) |
| **ncg1** | 0 B | **uninitialized data (`.bss`)** | raw size 0; space reserved only at load time |
| **ncg2** | 302,592 B | **16-bit permutation / index table** | 151,296 `u16`; `arr[i]=i` up to idx 2835 then scattered swaps (e.g. 2836,2837,**2835**) |
| **ncg3** | 8,192 B | **pointer / encrypted data table** | `u32[2048]`, 1,050 non-zero; starts with in-image pointers `0x105f7018/18/1c/20`, then encrypted-looking constants |
| **ncg4** | 2,048 B | **debug directory + CodeView PDB record** | `RSDS` signature, GUID/age/PDB path above; preceding records use RVAs `0x5f90xx`/`0x1d62xx` |
| **ncg5** | 512 B | **`.rsrc` — resources** | resource dir header (LANGID `0x0409` en-US) + `RT_MANIFEST` SxS manifest |

## ncg5 manifest (full)
```xml
<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<assembly xmlns='urn:schemas-microsoft-com:asm.v1' manifestVersion='1.0'>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level='asInvoker' uiAccess='false' />
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>
```
Standard `asInvoker` manifest — no elevation, no extra dependencies declared.

## Summary
- This is **not an archive**; the `.bin` files are **raw PE sections** of one protected
  32-bit DLL (`Core.dll`).
- Only **ncg0** holds executable code and only it is obfuscated (control-flow
  jump-threading, ~10.8% real code). ncg1–ncg5 are plain PE data: bss, two
  lookup/pointer tables, the debug/PDB record, and the resource manifest.
- Identifying artifacts recovered: **module = Core.dll**, **PDB GUID 2CDAF256-…-F537**,
  **build path `D:\Work\JP_D10_260826_Patch\Client\Core\Lib\`**.
