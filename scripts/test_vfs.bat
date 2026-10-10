@echo off
rem Stage 3: run the emulator with different VFS variants.
setlocal
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src
set VFS=%ROOT%\examples\vfs
set SCRIPT=%ROOT%\examples\scripts\stage3.txt

echo ===== default in-memory VFS =====
python -m emulator --script "%SCRIPT%"

echo ===== minimal VFS =====
python -m emulator --vfs "%VFS%\minimal.xml" --script "%SCRIPT%"

echo ===== several files =====
python -m emulator --vfs "%VFS%\several_files.xml" --script "%SCRIPT%"

echo ===== 3+ levels of nesting =====
python -m emulator --vfs "%VFS%\deep.xml" --script "%SCRIPT%"

echo ===== error: file not found =====
python -m emulator --vfs "%VFS%\missing.xml" --script "%SCRIPT%"
echo exit code: %ERRORLEVEL%

echo ===== error: invalid XML =====
python -m emulator --vfs "%VFS%\broken.xml" --script "%SCRIPT%"
echo exit code: %ERRORLEVEL%

echo ===== error: invalid base64 =====
python -m emulator --vfs "%VFS%\bad_base64.xml" --script "%SCRIPT%"
echo exit code: %ERRORLEVEL%
endlocal
