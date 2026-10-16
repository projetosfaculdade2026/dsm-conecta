#!/usr/bin/env bash
# Gera os artefatos (navegador e Android; desktop do sistema atual). Uso: ./build_artefatos.sh [URL_DA_API]
set -euo pipefail
cd "$(dirname "$0")/app"
API="${1:-http://localhost:8000}"
[ -d web ] || flutter create . --project-name dsm_conecta --platforms=web,android,linux
rm -f test/widget_test.dart
dart tool/preparar_plataformas.dart
flutter pub get
rm -rf ../dist && mkdir -p ../dist
flutter build web --release --dart-define=API_URL="$API"
rm -rf ../web && cp -r build/web ../web && cp -r build/web ../dist/web
flutter build apk --release --dart-define=API_URL="$API" && cp build/app/outputs/flutter-apk/app-release.apk ../dist/dsm-conecta.apk || echo "APK nao gerado (falta Android SDK)"
echo "Pronto: dist/ e web/ (servido pela API em http://localhost:8000)"
