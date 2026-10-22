@echo off
setlocal
pushd "%~dp0"
if not exist .venv\Scripts\python.exe (
  call Setup.cmd
  if errorlevel 1 (
    echo Setup failed. Check the error above.
    pause
    popd
    exit /b 1
  )
)
.venv\Scripts\python.exe main.py
set "run_result=%errorlevel%"
if not "%run_result%"=="0" pause
popd
exit /b %run_result%
