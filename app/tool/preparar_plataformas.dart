// Ajusta os arquivos gerados pelo "flutter create" para o que o app precisa.
// Uso (dentro da pasta app):  dart tool/preparar_plataformas.dart
import 'dart:io';

const permissoes = [
  '<uses-permission android:name="android.permission.INTERNET"/>',
  '<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>',
  '<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>',
];

void main() {
  final f = File('android/app/src/main/AndroidManifest.xml');
  if (!f.existsSync()) {
    stdout.writeln('Android não gerado; nada a ajustar.');
    return;
  }
  var xml = f.readAsStringSync();
  final faltando = permissoes.where((p) => !xml.contains(p.split('"')[1])).toList();
  if (faltando.isNotEmpty) {
    xml = xml.replaceFirst('<application', '${faltando.join('\n    ')}\n    <application');
  }
  // O app conversa com a API em http durante o desenvolvimento (use https em produção).
  if (!xml.contains('usesCleartextTraffic')) {
    xml = xml.replaceFirst('<application', '<application\n        android:usesCleartextTraffic="true"');
  }
  f.writeAsStringSync(xml);
  stdout.writeln('AndroidManifest.xml ajustado (internet, localização).');
}
