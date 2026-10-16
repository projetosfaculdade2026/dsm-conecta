@echo off
setlocal
cd /d "%~dp0app"
where flutter >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Flutter nao encontrado. Instale: https://docs.flutter.dev/get-started/install/windows
  echo Depois feche e abra o terminal/explorador de novo.
  pause
  exit /b 1
)
if not exist web (
  echo Primeira execucao: gerando pastas de plataforma...
  call flutter create . --project-name dsm_conecta --platforms=web,android,windows
)
if exist test\widget_test.dart del test\widget_test.dart
call dart tool\preparar_plataformas.dart
call flutter pub get
echo Abrindo o aplicativo no Chrome...
call flutter run -d chrome
pause
