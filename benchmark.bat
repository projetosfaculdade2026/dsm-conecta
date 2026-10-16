@echo off
cd /d "%~dp0"
echo Carga sintetica de 1 milhao de registros + comparativo de desempenho (pode levar alguns minutos)
docker compose run --rm api python -m app.bench --n 1000000
pause
