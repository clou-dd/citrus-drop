@echo off
setlocal
pushd "%~dp0"
if not exist CitrusDrop.exe (
  call build.cmd
  if errorlevel 1 (
    echo Build failed. Please keep the error message for troubleshooting.
    pause
    popd
    exit /b 1
  )
)
start "" "%~dp0CitrusDrop.exe"
popd
