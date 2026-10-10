@echo off
rem Stage 2: test all supported command line options.
setlocal
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src

echo ===== 1. help =====
python -m emulator --help

echo ===== 2. no options (stdin is empty) =====
python -m emulator < nul

echo ===== 3. --script only =====
python -m emulator --script "%ROOT%\examples\scripts\stage2.txt"

echo ===== 4. --vfs and --script =====
python -m emulator --vfs "%ROOT%\examples\vfs\deep.xml" --script "%ROOT%\examples\scripts\stage2.txt"

echo ===== 5. missing script file =====
python -m emulator --script "%ROOT%\examples\scripts\missing.txt"
echo exit code: %ERRORLEVEL%

echo ===== 6. unknown option =====
python -m emulator --bad-option
echo exit code: %ERRORLEVEL%
endlocal
