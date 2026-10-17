@echo off
rem ============================================================================
rem build_msvc.bat - build the proxy/shim DLL with the MSVC toolchain.
rem
rem Run this from a "x64 Native Tools Command Prompt for VS" (or the x86 one
rem for a 32-bit target) so that cl.exe and link.exe are on PATH, and with
rem python on PATH.
rem
rem Usage:
rem   build_msvc.bat path\to\Original.dll [Name]
rem
rem   Name  Optional base name for the shim (default: original's base name).
rem
rem Produces, in the .\build directory:
rem   <Name>.dll        the shim (deploy under the original's name)
rem   <Name>_orig.dll   a copy of the real original the shim forwards to
rem
rem Unlike the MinGW build, this uses --ordinal-forward, so ordinal-only
rem (NONAME) exports are also proxied (MSVC supports ordinal forwarders).
rem ============================================================================
setlocal enabledelayedexpansion

set "HERE=%~dp0"
set "ORIG_PATH=%~1"
if "%ORIG_PATH%"=="" (
  echo error: path to the original DLL is required
  echo usage: %~nx0 path\to\Original.dll [Name]
  exit /b 2
)
if not exist "%ORIG_PATH%" (
  echo error: no such file: %ORIG_PATH%
  exit /b 2
)

set "NAME=%~2"
if "%NAME%"=="" set "NAME=%~n1"
set "ORIG_NAME=%NAME%_orig"
set "OUT=build"

if not exist "%OUT%" mkdir "%OUT%"
set "DEF=%OUT%\%NAME%.def"
set "CFG=%OUT%\gen_config.h"

echo ^>^> generating export forwarders: %DEF%
python "%HERE%gen_def.py" "%ORIG_PATH%" --orig-name "%ORIG_NAME%" --ordinal-forward -o "%DEF%"
if errorlevel 1 exit /b 1

rem Write build-time config into a forced-include header (avoids /D quoting).
> "%CFG%" echo #define ORIG_DLL_NAME "%ORIG_NAME%"
>> "%CFG%" echo #define SHIM_NAME "%NAME%-shim"

echo ^>^> copying original -^> %OUT%\%ORIG_NAME%.dll
copy /y "%ORIG_PATH%" "%OUT%\%ORIG_NAME%.dll" >nul

echo ^>^> compiling shim -^> %OUT%\%NAME%.dll
cl /nologo /O2 /LD /I "%HERE%." /FI "%CFG%" ^
   "%HERE%shim.c" ^
   /Fo"%OUT%\\" /Fe"%OUT%\%NAME%.dll" ^
   /link /DEF:"%DEF%"
if errorlevel 1 exit /b 1

echo.
echo done. deploy BOTH files next to the host program:
echo     %OUT%\%NAME%.dll        (replaces the original %NAME%.dll)
echo     %OUT%\%ORIG_NAME%.dll   (the real original, renamed)
endlocal
