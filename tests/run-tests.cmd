@echo off
setlocal
pushd "%~dp0.."
call Setup.cmd
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements-dev.txt
if errorlevel 1 exit /b 1
set "QT_QPA_PLATFORM=offscreen"
.venv\Scripts\python.exe -m pytest -q
set "test_result=%errorlevel%"
if /i not "%~1"=="--no-pause" pause
popd
exit /b %test_result%
