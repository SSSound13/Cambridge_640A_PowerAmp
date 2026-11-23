@echo off
setlocal
cd /d "%~dp0"
set "KICAD_PYTHON=%LOCALAPPDATA%\Programs\KiCad\10.0\bin\python.exe"
if not exist "%KICAD_PYTHON%" set "KICAD_PYTHON=%ProgramFiles%\KiCad\10.0\bin\python.exe"
if not exist "%KICAD_PYTHON%" (
  echo KiCad 10 Python was not found. Install KiCad or update the path in this file.
  pause
  exit /b 1
)
echo Save both editable boards before running this command.
echo VolumeControl.kicad_pcb is generated and will be replaced.
"%KICAD_PYTHON%" "%~dp0sync_mechanical.py"
if errorlevel 1 (
  echo Assembly update failed.
  pause
  exit /b 1
)
echo Assembly updated. Reopen VolumeControl.kicad_pcb and its 3D Viewer.
pause
