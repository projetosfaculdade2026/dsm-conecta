import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:dsm_conecta/a11y.dart';

void main() {
  test('contraste: preto sobre branco é 21:1 e cor igual é 1:1', () {
    expect(contrastRatio(Colors.black, Colors.white), closeTo(21, 0.01));
    expect(contrastRatio(Colors.white, Colors.white), closeTo(1, 0.01));
  });

  test('RNF19: pares de cores do tema têm contraste mínimo de 4,5:1', () {
    final c = temaDsm().colorScheme;
    final pares = {
      'onPrimary/primary': [c.onPrimary, c.primary],
      'onSurface/surface': [c.onSurface, c.surface],
      'onSurfaceVariant/surface': [c.onSurfaceVariant, c.surface],
      'onError/error': [c.onError, c.error],
      'onPrimaryContainer/primaryContainer': [c.onPrimaryContainer, c.primaryContainer],
      'onSecondaryContainer/secondaryContainer': [c.onSecondaryContainer, c.secondaryContainer],
    };
    pares.forEach((nome, cores) {
      expect(contrastRatio(cores[0], cores[1]), greaterThanOrEqualTo(4.5), reason: nome);
    });
  });

  test('a cor primária escolhida passa no nível AAA (7:1) com texto branco', () {
    expect(contrastRatio(Colors.white, corPrimaria), greaterThanOrEqualTo(7));
  });

  test('escala de fonte fica entre o mínimo e o máximo', () {
    expect(escalaValida(0.1), escalaMinima);
    expect(escalaValida(9), escalaMaxima);
    expect(escalaValida(1.3), 1.3);
  });
}
