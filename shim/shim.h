/*
 * shim.h - public surface of the shim's own code.
 *
 * The export *forwarding* is done entirely by the generated .def file and the
 * Windows loader; none of the original API is reimplemented here.  This header
 * only declares the small amount of code the shim runs for itself: lifecycle
 * hooks and a lazy handle to the original DLL for any interception you add.
 */
#ifndef SHIM_H
#define SHIM_H

#define WIN32_LEAN_AND_MEAN
#include <windows.h>

/*
 * Returns a handle to the renamed original DLL (ORIG_DLL_NAME), loading it on
 * first use.  Use it with GetProcAddress when you want to *call* the original
 * from inside the shim (as opposed to merely forwarding, which the .def already
 * handles).  Returns NULL if the original cannot be found.
 */
HMODULE Shim_GetOriginal(void);

/*
 * Called once from DllMain on DLL_PROCESS_ATTACH, after logging is set up.
 * Put your own initialization / hook installation here.  Return FALSE to abort
 * loading of the shim (which will fail the host process's load of the DLL).
 */
BOOL Shim_OnAttach(void);

/* Called once from DllMain on DLL_PROCESS_DETACH for cleanup. */
void Shim_OnDetach(void);

/* Append a line to the shim log (no-op when SHIM_ENABLE_LOG == 0). */
void Shim_Log(const char *fmt, ...);

#endif /* SHIM_H */
