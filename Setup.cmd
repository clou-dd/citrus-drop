@echo off
setlocal
pushd "%~dp0"
set "python_launcher=py -3"
where py >nul 2>nul
if errorlevel 1 set "python_launcher=python"
if not exist .venv\Scripts\python.exe (
  %python_launcher% -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)"
  if errorlevel 1 (
    echo Python 3.11, 3.12, or 3.13 for Windows x64 is required.
    popd
    exit /b 1
  )
  %python_launcher% -m venv .venv
  if errorlevel 1 (
    popd
    exit /b 1
  )
)
.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements.txt
set "setup_result=%errorlevel%"
popd
exit /b %setup_result%
