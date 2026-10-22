@echo off
setlocal
pushd "%~dp0.."
set "framework_dir=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319"
if not exist "%framework_dir%\csc.exe" set "framework_dir=%WINDIR%\Microsoft.NET\Framework\v4.0.30319"
if not exist "%framework_dir%\csc.exe" (
  echo .NET Framework C# compiler not found.
  if /i not "%~1"=="--no-pause" pause
  popd
  exit /b 1
)
"%framework_dir%\csc.exe" /nologo /codepage:65001 /utf8output /langversion:5 /target:exe /out:tests\CitrusDrop.Tests.exe /r:"%framework_dir%\System.dll" /r:"%framework_dir%\System.Core.dll" /r:"%framework_dir%\System.IO.Compression.dll" /r:"%framework_dir%\System.IO.Compression.FileSystem.dll" /r:"%framework_dir%\WPF\WindowsBase.dll" /r:"%framework_dir%\WPF\PresentationCore.dll" src\Core.cs src\Converter.cs src\PdfTools.cs src\PdfImages.cs src\PdfDocumentWriter.cs tests\SmokeTests.cs
if errorlevel 1 (
  if /i not "%~1"=="--no-pause" pause
  popd
  exit /b 1
)
tests\CitrusDrop.Tests.exe
set "test_result=%errorlevel%"
if /i not "%~1"=="--no-pause" pause
popd
exit /b %test_result%
