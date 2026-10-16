@echo off
rem Publica o conjunto de dados abertos no repositorio (RNF03, Iteracao 6): baixa os arquivos da API em dados-abertos\
cd /d "%~dp0"
if not exist dados-abertos mkdir dados-abertos
curl -s -f -o dados-abertos\telemetria_agregada.csv "http://localhost:8000/open-data/telemetria?format=csv"
if errorlevel 1 (echo [ERRO] API fora do ar. Rode iniciar.bat primeiro. & pause & exit /b 1)
curl -s -f -o dados-abertos\telemetria_agregada.json "http://localhost:8000/open-data/telemetria?format=json"
curl -s -f -o dados-abertos\dicionario_de_dados.json http://localhost:8000/open-data/dicionario
echo Arquivos gerados em dados-abertos\ (inclua-os no commit). Somente agregados com no minimo 10 registros por grupo.
pause
