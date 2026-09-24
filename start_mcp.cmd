@echo off
setlocal
cd /d "%~dp0"
if not defined SODAM_RHINO_WORKSPACE set "SODAM_RHINO_WORKSPACE=%~dp0workspace"
if not defined SODAM_BLENDER_EXE if exist "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" set "SODAM_BLENDER_EXE=C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
"%~dp0.venv\Scripts\python.exe" -m sodam_rhino_mcp.server
