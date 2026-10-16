@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo   DSM Conecta - iniciando o back-end
echo ==========================================
docker --version >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Docker nao encontrado. Instale o Docker Desktop: https://www.docker.com/products/docker-desktop
  pause
  exit /b 1
)
docker info >nul 2>&1
if errorlevel 1 (
  echo [ERRO] O Docker Desktop nao esta rodando.
  echo Abra o Docker Desktop, espere o icone ficar verde e execute este arquivo de novo.
  pause
  exit /b 1
)
echo Subindo broker, banco, ingestao, API e totem simulado...
echo (na primeira vez demora varios minutos para baixar as imagens)
docker compose up --build -d
if errorlevel 1 (
  echo [ERRO] Falha ao subir. Veja a mensagem acima. Tente: docker compose down -v
  pause
  exit /b 1
)
set /a tentativas=0
:espera
set /a tentativas+=1
if %tentativas% gtr 60 (
  echo [ERRO] A API nao respondeu a tempo. Rode: docker compose logs api
  pause
  exit /b 1
)
timeout /t 3 /nobreak >nul
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 goto espera
echo.
echo PRONTO! Back-end no ar.
echo   Documentacao da API: http://localhost:8000/docs
echo   Login admin: admin / admin123
echo   Totem simulado no navegador: http://localhost:8000/simulador/
echo   Dados abertos (sem login): http://localhost:8000/open-data/telemetria
echo Agora execute app.bat para abrir o aplicativo.
start http://localhost:8000/docs
pause
