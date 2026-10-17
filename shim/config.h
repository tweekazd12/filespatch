/*
 * config.h - compile-time configuration for the proxy/shim DLL.
 *
 * Edit the values here (or override them with -D flags on the compiler
 * command line) to match your target.  The two names below MUST agree with
 * the arguments you pass to gen_def.py when generating the forwarder table.
 */
#ifndef SHIM_CONFIG_H
#define SHIM_CONFIG_H

/*
 * ORIG_DLL_NAME is the module the forwarders point at - i.e. the renamed copy
 * of the original DLL that sits next to this shim.  No ".dll" extension and no
 * path: the Windows loader resolves it like any other module name.
 *
 * Example: ship the real file as "Core_orig.dll" and keep this as "Core_orig".
 */
#ifndef ORIG_DLL_NAME
#define ORIG_DLL_NAME "Core_orig"
#endif

/* Human-readable name used only in log lines. */
#ifndef SHIM_NAME
#define SHIM_NAME "Core-shim"
#endif

/*
 * SHIM_ENABLE_LOG: when 1, DllMain writes a small log next to the shim DLL
 * (see SHIM_LOG_FILE) recording attach/detach.  Set to 0 for a silent shim.
 */
#ifndef SHIM_ENABLE_LOG
#define SHIM_ENABLE_LOG 1
#endif

/* Log file name, created in the same directory as the shim DLL. */
#ifndef SHIM_LOG_FILE
#define SHIM_LOG_FILE "Core-shim.log"
#endif

#endif /* SHIM_CONFIG_H */
