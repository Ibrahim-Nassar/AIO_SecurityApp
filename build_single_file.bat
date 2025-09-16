@echo off
setlocal
cd /d %~dp0
"%~dp0\..\..\..\..\..\..\..\..\%SystemRoot%\System32\where.exe" python >nul 2>&1
if errorlevel 1 (
  echo Python not found in PATH.
  exit /b 1
)
python tools\make_single.py
if errorlevel 1 exit /b 1
echo Done.


