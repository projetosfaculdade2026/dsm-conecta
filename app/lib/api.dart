import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// RNF10: o cliente só conhece esta URL (transparência de localização).
/// Para trocar: flutter run --dart-define=API_URL=http://192.168.0.10:8000
String get apiUrl {
  const d = String.fromEnvironment('API_URL');
  if (d.isNotEmpty) return d;
  if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
    return 'http://10.0.2.2:8000'; // emulador Android -> máquina host
  }
  return 'http://localhost:8000';
}

class ApiException implements Exception {
  final String msg;
  ApiException(this.msg);
  @override
  String toString() => msg;
}

class Api {
  Api._();
  static final Api i = Api._();
  String? token;

  Uri _u(String p) => Uri.parse('$apiUrl$p');
  Map<String, String> get _h => {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  /// Extrai a mensagem legível (campo "detail" da API) de um corpo de erro.
  static String detalhe(String corpo) {
    try {
      final d = jsonDecode(corpo);
      if (d is Map && d['detail'] != null) return d['detail'].toString();
    } catch (_) {
      // corpo não é JSON: devolve como veio
    }
    return corpo;
  }

  dynamic _dec(http.Response r) {
    final corpo = utf8.decode(r.bodyBytes);
    if (r.statusCode >= 400) throw ApiException(detalhe(corpo));
    return corpo.isEmpty ? null : jsonDecode(corpo);
  }

  Future<dynamic> _get(String p) async =>
      _dec(await http.get(_u(p), headers: _h).timeout(const Duration(seconds: 8)));

  /// RF08: se a rede falhar, usa a última resposta salva localmente.
  Future<dynamic> _getCached(String p, String chave) async {
    final prefs = await SharedPreferences.getInstance();
    try {
      final d = await _get(p);
      await prefs.setString(chave, jsonEncode(d));
      return d;
    } catch (_) {
      final c = prefs.getString(chave);
      if (c == null) rethrow;
      return jsonDecode(c);
    }
  }

  Future<List<dynamic>> content({String? kind}) async {
    final d = await _getCached('/content', 'cache_content') as List;
    return kind == null ? d : d.where((e) => e['kind'] == kind).toList();
  }

  Future<Map<String, dynamic>> quiz() async =>
      Map<String, dynamic>.from(await _getCached('/quiz', 'cache_quiz'));

  Future<Map<String, dynamic>> publicMetrics() async =>
      Map<String, dynamic>.from(await _get('/metrics/public'));

  Future<void> sendMessage(String nome, String texto) async {
    _dec(await http
        .post(_u('/messages'), headers: _h, body: jsonEncode({'nome': nome, 'texto': texto}))
        .timeout(const Duration(seconds: 8)));
  }

  /// Retorna o status HTTP (lança exceção se não houver rede).
  Future<int> postEvent(Map<String, dynamic> ev) async {
    final r = await http
        .post(_u('/events'), headers: _h, body: jsonEncode(ev))
        .timeout(const Duration(seconds: 8));
    if (r.statusCode >= 400) lastError = detalhe(utf8.decode(r.bodyBytes));
    return r.statusCode;
  }

  String lastError = '';

  Future<List<dynamic>> history(String sid) async => await _get('/sessions/$sid/history') as List;

  Future<void> deleteSession(String sid) async {
    _dec(await http.delete(_u('/sessions/$sid'), headers: _h).timeout(const Duration(seconds: 8)));
  }

  // ------------- administrativo
  Future<void> login(String u, String p) async {
    final d = _dec(await http
        .post(_u('/auth/login'), headers: _h, body: jsonEncode({'username': u, 'password': p}))
        .timeout(const Duration(seconds: 8)));
    token = d['access_token'] as String;
  }

  Future<List<dynamic>> adminContent() async => await _get('/admin/content') as List;

  Future<void> saveContent(Map<String, dynamic> c, {int? id}) async {
    final r = id == null
        ? await http.post(_u('/content'), headers: _h, body: jsonEncode(c))
        : await http.put(_u('/content/$id'), headers: _h, body: jsonEncode(c));
    _dec(r);
  }

  Future<void> deleteContent(int id) async => _dec(await http.delete(_u('/content/$id'), headers: _h));

  Future<String> export(String format) async {
    final r = await http.get(_u('/export?format=$format'), headers: _h);
    if (r.statusCode >= 400) _dec(r);
    return utf8.decode(r.bodyBytes);
  }

  /// RF20: janela deslizante configurável (segundos).
  Future<void> setJanela(int segundos) async {
    _dec(await http
        .put(_u('/admin/config'), headers: _h, body: jsonEncode({'janela_s': segundos}))
        .timeout(const Duration(seconds: 8)));
  }

  /// Devolutiva agregada para a escola parceira (Markdown).
  Future<String> relatorio() async {
    final r = await http.get(_u('/admin/report'), headers: _h).timeout(const Duration(seconds: 8));
    if (r.statusCode >= 400) _dec(r);
    return utf8.decode(r.bodyBytes);
  }

  /// Endereço público do conjunto de dados abertos (RNF03).
  String get dadosAbertosUrl => '$apiUrl/open-data/telemetria';

  Uri wsUri() => Uri.parse('${apiUrl.replaceFirst('http', 'ws')}/ws/live?token=$token');
}
