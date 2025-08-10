@echo off
cd /d %~dp0
call .venv\Scripts\activate
set FLASK_APP=mungrade_flask_starter.py
set FLASK_ENV=development
flask run
pause