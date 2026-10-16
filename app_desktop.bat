@echo off
setlocal
cd /d "%~dp0app"
if not exist windows (
  call flutter create . --project-name dsm_conecta --platforms=web,android,windows
)
if exist test\widget_test.dart del test\widget_test.dart
call dart tool\preparar_plataformas.dart
call flutter pub get
call flutter run -d windows
pause
