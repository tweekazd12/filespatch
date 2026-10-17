# "Frost" / secure-module references

Where Core.dll mentions Frost (found in the ncg2 symbol-name pool, demangled):

    public: int  __thiscall L2Configuration::GetFrostSecureModule(void) const
    public: void __thiscall L2Configuration::SetFrostSecureModule(int)

"Frost" is the client's **security / anti-cheat secure module**. These two are the
config accessors on `L2Configuration` that READ and WRITE the Frost-secure-module flag
(an `int`: get returns it, set takes it) - i.e. whether the Frost module is engaged.
They are the configuration hooks for it; the actual load/init call sites are reached
indirectly (through C++ virtual/field-pointer calls) and are not resolvable from these
static section dumps alone.

Related security / protection globals and flags seen in the same pool:
    int GIsGuarded              // SEH "guarded" execution flag
    int GL2UseTenProtect        // TenProtect (Tencent anti-cheat) enable flag

So the client references at least two protection systems by name: **Frost** (secure
module, via L2Configuration) and **TenProtect**. Only the names/accessors are visible
statically; nothing here decrypts or enables them.
