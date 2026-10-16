import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:sensors_plus/sensors_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';
import 'api.dart';
import 'localizacao.dart';

/// Telemetria com consentimento (RN01), sessão aleatória (RN02/RNF15)
/// e fila local para envio posterior quando não há rede (RNF11).
class Telemetry extends ChangeNotifier {
  Telemetry._();
  static final Telemetry i = Telemetry._();

  late SharedPreferences _p;
  bool consent = false;
  String? sessionId;
  List<Map<String, dynamic>> _fila = [];
  bool _busy = false;

  bool get decided => _p.containsKey('consent');
  int get pendentes => _fila.length;

  Future<void> init() async {
    _p = await SharedPreferences.getInstance();
    consent = _p.getBool('consent') ?? false;
    sessionId = _p.getString('session');
    _fila = (jsonDecode(_p.getString('fila') ?? '[]') as List)
        .map((e) => Map<String, dynamic>.from(e as Map))
        .toList();
    Timer.periodic(const Duration(seconds: 10), (_) => flush());
  }

  Future<void> setConsent(bool v) async {
    consent = v;
    await _p.setBool('consent', v);
    if (v && sessionId == null) {
      sessionId = const Uuid().v4(); // gerado localmente, aleatório
      await _p.setString('session', sessionId!);
    }
    notifyListeners();
  }

  Map<String, dynamic> _evento(String categoria, Map<String, dynamic> payload) => {
        'event_id': const Uuid().v4(),
        'session_id': sessionId,
        'categoria': categoria,
        'origem': 'app',
        'ts': DateTime.now().toUtc().toIso8601String(),
        'schema_version': 1,
        'payload': payload,
      };

  Future<void> _save() => _p.setString('fila', jsonEncode(_fila));

  Future<void> track(String categoria, Map<String, dynamic> payload) async {
    if (!consent || sessionId == null) return; // RN01
    _fila.add(_evento(categoria, payload));
    await _save();
    unawaited(flush());
  }

  Future<void> flush() async {
    if (_busy || _fila.isEmpty) return;
    _busy = true;
    try {
      while (_fila.isNotEmpty) {
        final s = await Api.i.postEvent(_fila.first);
        final descartar = s < 300 || (s >= 400 && s < 500 && s != 429);
        if (!descartar) break; // 5xx/429: mantém na fila e tenta depois
        _fila.removeAt(0);
        await _save();
      }
    } catch (_) {
      // sem rede: mantém na fila
    } finally {
      _busy = false;
      notifyListeners();
    }
  }

  /// Registro de presença por código do evento (RF10) ou por localização (RF11).
  /// O servidor aplica a janela de horário (RN03), o raio de 150 m (RN04) e a presença única (RN05).
  Future<String> presenca(int eventoId, {String? codigo, double? lat, double? lon}) async {
    if (!consent || sessionId == null) return 'Ative o consentimento em Privacidade para registrar presença.';
    final payload = <String, dynamic>{'evento_id': eventoId};
    if (codigo != null && codigo.trim().isNotEmpty) {
      payload['codigo'] = codigo.trim();
    } else if (lat != null && lon != null) {
      payload['lat'] = lat;
      payload['lon'] = lon;
    } else {
      return 'Informe o código do evento ou use a sua localização.';
    }
    try {
      final s = await Api.i.postEvent(_evento('presenca', payload));
      if (s < 300) return 'Presença registrada!';
      return 'Não foi possível registrar: ${Api.i.lastError}';
    } catch (_) {
      return 'Sem conexão. Tente novamente.';
    }
  }

  /// Presença por proximidade geográfica: pede a localização só neste momento (RF11).
  Future<String> presencaPorLocalizacao(int eventoId) async {
    if (!consent || sessionId == null) return 'Ative o consentimento em Privacidade para registrar presença.';
    try {
      final p = await posicaoAtual();
      return presenca(eventoId, lat: p.latitude, lon: p.longitude);
    } on LocalizacaoIndisponivel catch (e) {
      return e.toString();
    } catch (_) {
      return 'Não foi possível obter a localização.';
    }
  }

  /// Localização aproximada (arredondada a ~1 km) como leitura de sensor, mediante consentimento (RF14).
  Future<String> enviarLocalizacaoAproximada() async {
    if (!consent) return 'Ative o consentimento primeiro.';
    try {
      final p = await posicaoAtual();
      final valor = '${p.latitude.toStringAsFixed(2)},${p.longitude.toStringAsFixed(2)}';
      await track('sensor', {'tipo': 'localizacao_aproximada', 'valor': valor});
      return 'Localização aproximada enviada.';
    } on LocalizacaoIndisponivel catch (e) {
      return e.toString();
    } catch (_) {
      return 'Não foi possível obter a localização.';
    }
  }

  /// Leitura do acelerômetro mediante consentimento (RF14).
  Future<String> enviarSensor() async {
    if (!consent) return 'Ative o consentimento primeiro.';
    try {
      final e = await accelerometerEventStream().first.timeout(const Duration(seconds: 2));
      final v = sqrt(e.x * e.x + e.y * e.y + e.z * e.z);
      await track('sensor', {'tipo': 'acelerometro', 'valor': double.parse(v.toStringAsFixed(2))});
      return 'Leitura enviada: ${v.toStringAsFixed(2)} m/s²';
    } catch (_) {
      return 'Sensor indisponível neste dispositivo.';
    }
  }

  /// RF12 / RN02: apaga dados no servidor e descarta o identificador local.
  Future<void> excluirDados() async {
    final sid = sessionId;
    if (sid != null) await Api.i.deleteSession(sid);
    _fila.clear();
    await _save();
    await _p.remove('session');
    sessionId = null;
    consent = false;
    await _p.setBool('consent', false);
    notifyListeners();
  }
}
