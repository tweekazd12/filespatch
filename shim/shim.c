/*
 * shim.c - entry point and support code for the transparent proxy DLL.
 *
 * How the proxy works
 * -------------------
 * Every export of the original DLL is re-exported by this shim as a PE
 * "forwarder": the shim's export table entry for, say, Foo contains the string
 * "Core_orig.Foo" instead of a code address.  When any client imports Foo from
 * this DLL, the Windows loader transparently redirects the import to the
 * original.  This is handled entirely by the generated .def file and the
 * loader - it is correct for every calling convention, for data exports, and
 * for ordinal-only exports, and it costs nothing at call time.
 *
 * This file therefore does NOT reimplement the API.  It only runs the shim's
 * own code at load/unload time (DllMain -> Shim_OnAttach / Shim_OnDetach),
 * which is where you add logging, config loading, or hooks.
 */
#include "config.h"
#include "shim.h"

#include <stdio.h>
#include <stdarg.h>

static HMODULE g_self = NULL;        /* this shim's own module handle */
static HMODULE g_orig = NULL;        /* lazily-loaded original DLL     */

/* ---- logging ----------------------------------------------------------- */

#if SHIM_ENABLE_LOG
/* Build the absolute path of a sibling file next to this shim DLL. */
static BOOL sibling_path(const char *leaf, char *out, DWORD out_sz)
{
    char dir[MAX_PATH];
    DWORD n = GetModuleFileNameA(g_self, dir, (DWORD)sizeof(dir));
    if (n == 0 || n >= sizeof(dir))
        return FALSE;

    /* Strip the file name, keep the trailing backslash. */
    for (DWORD i = n; i > 0; --i) {
        if (dir[i - 1] == '\\' || dir[i - 1] == '/') {
            dir[i] = '\0';
            break;
        }
    }
    return _snprintf(out, out_sz, "%s%s", dir, leaf) > 0;
}
#endif

void Shim_Log(const char *fmt, ...)
{
#if SHIM_ENABLE_LOG
    char path[MAX_PATH];
    if (!sibling_path(SHIM_LOG_FILE, path, sizeof(path)))
        return;

    FILE *f = fopen(path, "a");
    if (!f)
        return;

    SYSTEMTIME st;
    GetLocalTime(&st);
    fprintf(f, "[%04u-%02u-%02u %02u:%02u:%02u] [" SHIM_NAME "] ",
            st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);

    va_list ap;
    va_start(ap, fmt);
    vfprintf(f, fmt, ap);
    va_end(ap);

    fputc('\n', f);
    fclose(f);
#else
    (void)fmt;
#endif
}

/* ---- access to the original DLL ---------------------------------------- */

HMODULE Shim_GetOriginal(void)
{
    if (!g_orig)
        g_orig = LoadLibraryA(ORIG_DLL_NAME ".dll");
    return g_orig;
}

/* ---- customization points ---------------------------------------------- */

BOOL Shim_OnAttach(void)
{
    /*
     * Add your initialization here.  For example, to call a function from the
     * original DLL:
     *
     *     HMODULE orig = Shim_GetOriginal();
     *     if (orig) {
     *         FARPROC p = GetProcAddress(orig, "SomeExport");
     *         ...
     *     }
     *
     * Returning FALSE here aborts the load of the shim.
     */
    return TRUE;
}

void Shim_OnDetach(void)
{
    /* Add your cleanup here. */
}

/* ---- entry point ------------------------------------------------------- */

BOOL WINAPI DllMain(HINSTANCE hinst, DWORD reason, LPVOID reserved)
{
    (void)reserved;

    switch (reason) {
    case DLL_PROCESS_ATTACH:
        g_self = (HMODULE)hinst;
        /* We do no per-thread work, so skip the thread notifications. */
        DisableThreadLibraryCalls(hinst);
        Shim_Log("attach (forwarding to %s.dll)", ORIG_DLL_NAME);
        if (!Shim_OnAttach()) {
            Shim_Log("Shim_OnAttach returned FALSE, aborting load");
            return FALSE;
        }
        break;

    case DLL_PROCESS_DETACH:
        Shim_OnDetach();
        Shim_Log("detach");
        if (g_orig) {
            FreeLibrary(g_orig);
            g_orig = NULL;
        }
        break;
    }
    return TRUE;
}
