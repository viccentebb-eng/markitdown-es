@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Integrar-con-Windows.ps1" -SourceDirectory "%~dp0."
if errorlevel 1 pause
