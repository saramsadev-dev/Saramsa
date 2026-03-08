@echo off
REM Saramsa Service Manager - Batch Wrapper
REM Usage: saramsa start

powershell.exe -ExecutionPolicy Bypass -File "%~dp0saramsa.ps1" %*
