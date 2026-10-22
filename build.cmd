@echo off
setlocal
pushd "%~dp0"
set "framework_dir=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319"
if not exist "%framework_dir%\csc.exe" set "framework_dir=%WINDIR%\Microsoft.NET\Framework\v4.0.30319"
if not exist "%framework_dir%\csc.exe" (
  echo C# compiler not found. This app requires Windows with .NET Framework 4.8.
  popd
  exit /b 1
)
if not exist "%framework_dir%\WPF\PresentationFramework.dll" (
  echo WPF runtime not found. Enable or install .NET Framework 4.8.
  popd
  exit /b 1
)
"%framework_dir%\csc.exe" /nologo /codepage:65001 /utf8output /langversion:5 /target:winexe /platform:anycpu /optimize+ /win32manifest:app.manifest /out:CitrusDrop.exe /r:"%framework_dir%\System.dll" /r:"%framework_dir%\System.Core.dll" /r:"%framework_dir%\System.Drawing.dll" /r:"%framework_dir%\System.Windows.Forms.dll" /r:"%framework_dir%\System.Xaml.dll" /r:"%framework_dir%\System.IO.Compression.dll" /r:"%framework_dir%\System.IO.Compression.FileSystem.dll" /r:"%framework_dir%\WPF\WindowsBase.dll" /r:"%framework_dir%\WPF\PresentationCore.dll" /r:"%framework_dir%\WPF\PresentationFramework.dll" src\*.cs
set "build_result=%errorlevel%"
if "%build_result%"=="0" echo Build completed: CitrusDrop.exe
popd
exit /b %build_result%
