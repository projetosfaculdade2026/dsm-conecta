@echo off
cd /d "%~dp0"
docker compose down
echo Servicos parados. (Para apagar tambem os dados: docker compose down -v)
pause
