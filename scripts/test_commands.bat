@echo off
rem Stages 4-5: run startup scripts that test emulator commands.
setlocal
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src
set VFS=%ROOT%\examples\vfs\deep.xml

for %%S in (stage4 stage5) do (
    if exist "%ROOT%\examples\scripts\%%S.txt" (
        echo ===== %%S =====
        python -m emulator --vfs "%VFS%" --script "%ROOT%\examples\scripts\%%S.txt"
    )
)
endlocal
