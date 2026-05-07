@echo off
cd /d "%~dp0"
call C:\CT\GITHUBREPO\PythonScripts\.venv\Scripts\activate.bat
python -m app auth
pause
