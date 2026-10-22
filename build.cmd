@echo off
setlocal
pushd "%~dp0"
call Setup.cmd
if errorlevel 1 (
  pause
  popd
  exit /b 1
)
.venv\Scripts\python.exe -m pip install --disable-pip-version-check PyInstaller==6.22.3
if errorlevel 1 (
  pause
  popd
  exit /b 1
)
.venv\Scripts\python.exe -m PyInstaller --noconfirm CitrusDrop.spec
set "build_result=%errorlevel%"
if "%build_result%"=="0" echo Build complete: dist\CitrusDrop\CitrusDrop.exe
if not "%build_result%"=="0" pause
popd
exit /b %build_result%
