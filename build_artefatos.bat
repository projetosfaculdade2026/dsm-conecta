@echo off
rem Gera os artefatos das 3 plataformas (Iteracao 5): navegador, Android (APK) e Windows.
rem Uso: build_artefatos.bat [URL_DA_API]     (padrao: http://localhost:8000)
setlocal
cd /d "%~dp0app"
set API=%1
if "%API%"=="" set API=http://localhost:8000
where flutter >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Flutter nao encontrado. Instale: https://docs.flutter.dev/get-started/install/windows
  pause & exit /b 1
)
if not exist web call flutter create . --project-name dsm_conecta --platforms=web,android,windows
if exist test\widget_test.dart del test\widget_test.dart
call dart tool\preparar_plataformas.dart
call flutter pub get
if exist ..\dist rmdir /s /q ..\dist
mkdir ..\dist

echo === Navegador ===
call flutter build web --release --dart-define=API_URL=%API%
if errorlevel 1 goto erro
xcopy /e /i /y build\web ..\web >nul
xcopy /e /i /y build\web ..\dist\web >nul

echo === Windows ===
call flutter build windows --release --dart-define=API_URL=%API%
if errorlevel 1 (echo [AVISO] Windows nao gerado: precisa do Visual Studio com "Desenvolvimento para desktop com C++".) else xcopy /e /i /y build\windows\x64\runner\Release ..\dist\windows >nul

echo === Android (APK) ===
call flutter build apk --release --dart-define=API_URL=%API%
if errorlevel 1 (echo [AVISO] APK nao gerado: precisa do Android SDK ^(Android Studio^).) else copy /y build\app\outputs\flutter-apk\app-release.apk ..\dist\dsm-conecta.apk >nul

echo.
echo Pronto. Artefatos em dist\ ; o build web tambem foi copiado para web\ e a API o serve em http://localhost:8000
pause
exit /b 0
:erro
echo [ERRO] Falha no build. Veja a mensagem acima.
pause
exit /b 1
