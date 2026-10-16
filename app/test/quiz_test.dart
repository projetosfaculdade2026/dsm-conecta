import 'package:flutter_test/flutter_test.dart';
import 'package:dsm_conecta/quiz_logic.dart';

void main() {
  test('perfil mais frequente vence', () {
    expect(perfilVencedor(['web', 'dados', 'dados', 'infra']), 'dados');
  });
  test('empate mantém o primeiro', () {
    expect(perfilVencedor(['web', 'dados', 'web', 'dados']), 'web');
  });
  test('lista vazia é erro', () {
    expect(() => perfilVencedor([]), throwsArgumentError);
  });
}
