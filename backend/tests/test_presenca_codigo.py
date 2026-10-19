from datetime import datetime, timezone

from app.rules import presenca_valida

EXTRA = {"inicio": "2026-09-01T00:00:00+00:00", "fim": "2026-09-02T00:00:00+00:00", "codigo": "DSM2026"}
AGORA = datetime(2026, 9, 1, 12, tzinfo=timezone.utc)


def test_codigo_ignora_maiusculas_e_minusculas():  # RF10: quem digita "dsm2026" também registra presença
    assert presenca_valida(EXTRA, AGORA, "dsm2026")[0]


def test_codigo_ignora_espacos_nas_pontas():
    assert presenca_valida(EXTRA, AGORA, "  DSM2026 ")[0]


def test_codigo_diferente_continua_invalido():
    ok, motivo = presenca_valida(EXTRA, AGORA, "DSM2027")
    assert not ok and "inválido" in motivo
