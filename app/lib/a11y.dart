import 'dart:math' as math;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Razão de contraste (WCAG 2.1) entre duas cores: de 1 a 21. O mínimo para texto comum é 4,5.
double contrastRatio(Color a, Color b) {
  final la = a.computeLuminance();
  final lb = b.computeLuminance();
  return (math.max(la, lb) + 0.05) / (math.min(la, lb) + 0.05);
}

const Color corPrimaria = Color(0xFF8E0000); // vinho: texto branco sobre ela tem contraste acima de 9:1

/// Tema do aplicativo (RNF19): contraste adequado e áreas de toque ampliadas.
ThemeData temaDsm() {
  final esquema = ColorScheme.fromSeed(seedColor: corPrimaria).copyWith(primary: corPrimaria, onPrimary: Colors.white);
  return ThemeData(
    colorScheme: esquema,
    useMaterial3: true,
    materialTapTargetSize: MaterialTapTargetSize.padded,
  );
}

const double escalaMinima = 0.85;
const double escalaMaxima = 2.0;

/// Mantém a escala dentro dos limites suportados pela interface.
double escalaValida(double v) => v.clamp(escalaMinima, escalaMaxima).toDouble();

/// Preferência de tamanho de fonte do usuário (RNF19). Soma-se ao ajuste de fonte do sistema.
class Acessibilidade extends ChangeNotifier {
  Acessibilidade._();
  static final Acessibilidade i = Acessibilidade._();

  double escala = 1.0;

  Future<void> init() async {
    final p = await SharedPreferences.getInstance();
    escala = escalaValida(p.getDouble('escala_fonte') ?? 1.0);
  }

  Future<void> definir(double v) async {
    escala = escalaValida(v);
    notifyListeners();
    final p = await SharedPreferences.getInstance();
    await p.setDouble('escala_fonte', escala);
  }
}
