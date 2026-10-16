@echo off
cd /d "%~dp0"
echo ==========================================================
echo Ensaio 1: 50 msg/s, 3000 mensagens, 1000 sessoes (1 conexao)
echo ==========================================================
docker compose run --rm api python -m app.simulator carga --taxa 50 --total 3000 --sessoes 1000
echo.
echo ==========================================================
echo Ensaio 2 (RNF06): 50 msg/s com 1000 CONEXOES MQTT reais
echo ==========================================================
docker compose run --rm api python -m app.simulator carga --taxa 50 --total 3000 --conexoes 1000
echo.
echo Copie as linhas "RESULTADO" para o relatorio (meta: perdidas=0).
pause
