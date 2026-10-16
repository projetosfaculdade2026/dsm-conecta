import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:dsm_conecta/consent_text.dart';
import 'package:dsm_conecta/telemetry.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('o termo cita a LGPD, a revogação e a exclusão dos dados', () {
    final texto = termoConsentimento.join(' ');
    expect(texto, contains('13.709/2018'));
    expect(texto, contains('revogar'));
    expect(texto, contains('excluir'));
    expect(termoConsentimento.length, greaterThanOrEqualTo(8));
  });

  test('RN01: sem consentimento nenhum evento entra na fila de envio', () async {
    SharedPreferences.setMockInitialValues({});
    await Telemetry.i.init();
    expect(Telemetry.i.consent, isFalse);
    await Telemetry.i.track('interacao', {'tela': 'inicio'});
    expect(Telemetry.i.pendentes, 0);
  });

  test('presença exige consentimento antes de qualquer envio', () async {
    SharedPreferences.setMockInitialValues({});
    await Telemetry.i.init();
    final msg = await Telemetry.i.presenca(1, codigo: 'DSM2026');
    expect(msg, contains('consentimento'));
  });
}
