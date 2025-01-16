@echo off
set RUTA_ACTUAL=%cd%
IF NOT EXIST "%RUTA_ACTUAL%\venv" (
    python -m venv "%RUTA_ACTUAL%\venv"
)
call "%RUTA_ACTUAL%\venv\Scripts\activate"
pip install -r requi.txt
start cmd /k "python manage.py runserver"
timeout /t 1
start http://127.0.0.1:8000/
