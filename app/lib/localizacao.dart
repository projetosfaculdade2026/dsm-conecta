import 'package:geolocator/geolocator.dart';

class LocalizacaoIndisponivel implements Exception {
  final String motivo;
  const LocalizacaoIndisponivel(this.motivo);
  @override
  String toString() => motivo;
}

/// Posição atual do aparelho, pedida somente quando o visitante escolhe usar a localização (RF11, RF14).
Future<Position> posicaoAtual() async {
  if (!await Geolocator.isLocationServiceEnabled()) {
    throw const LocalizacaoIndisponivel('Ative a localização do aparelho.');
  }
  var permissao = await Geolocator.checkPermission();
  if (permissao == LocationPermission.denied) {
    permissao = await Geolocator.requestPermission();
  }
  if (permissao == LocationPermission.denied || permissao == LocationPermission.deniedForever) {
    throw const LocalizacaoIndisponivel('Permissão de localização negada.');
  }
  return Geolocator.getCurrentPosition(
    locationSettings: const LocationSettings(accuracy: LocationAccuracy.high, timeLimit: Duration(seconds: 12)),
  );
}
