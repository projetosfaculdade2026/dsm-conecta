@echo off
cd /d "%~dp0backend"
python --version >nul 2>&1
if errorlevel 1 goto sempython
python -m pip install -q -r requirements-dev.txt
python -m ruff check .
python -m pytest --cov --cov-fail-under=70
pause
exit /b 0

:sempython
echo [ERRO] Python nao encontrado. Instale em https://www.python.org e marque Add python.exe to PATH.
pause
exit /b 1