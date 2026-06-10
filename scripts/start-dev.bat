@echo off
setlocal
pushd "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dev.ps1" %*
set EXITCODE=%ERRORLEVEL%
popd
exit /b %EXITCODE%
