from datetime import datetime, timezone

from app.rules import dentro_do_raio, mascarar_grupo, presenca_valida

EXTRA = {"inicio": "2026-09-01T00:00:00+00:00", "fim": "2026-09-02T00:00:00+00:00", "codigo": "ABC"}


def test_presenca_dentro_da_janela():
    assert presenca_valida(EXTRA, datetime(2026, 9, 1, 12, tzinfo=timezone.utc), "ABC")[0]


def test_presenca_fora_da_janela():
    ok, motivo = presenca_valida(EXTRA, datetime(2026, 9, 3, tzinfo=timezone.utc), "ABC")
    assert not ok and "janela" in motivo


def test_presenca_codigo_errado():
    assert not presenca_valida(EXTRA, datetime(2026, 9, 1, 12, tzinfo=timezone.utc), "XYZ")[0]


def test_raio_150m():
    assert dentro_do_raio(-23.6500, -46.6300, -23.6505, -46.6300)       # ~55 m
    assert not dentro_do_raio(-23.6500, -46.6300, -23.6600, -46.6300)   # ~1,1 km


def test_mascara_minimo_dez():
    linhas = [{"g": "a", "total": 9}, {"g": "b", "total": 10}]
    assert mascarar_grupo(linhas) == [{"g": "b", "total": 10}]


LOCAL = {"inicio": "2026-09-01T00:00:00+00:00", "fim": "2026-09-02T00:00:00+00:00", "lat": -23.6500, "lon": -46.6300}
AGORA = datetime(2026, 9, 1, 12, tzinfo=timezone.utc)


def test_presenca_por_localizacao_dentro_do_raio():  # RF11 / RN04
    assert presenca_valida(LOCAL, AGORA, None, -23.6505, -46.6300)[0]


def test_presenca_por_localizacao_fora_do_raio():
    ok, motivo = presenca_valida(LOCAL, AGORA, None, -23.6600, -46.6300)
    assert not ok and "raio" in motivo


def test_localizacao_respeita_a_janela_de_horario():  # RN03 vale também para a localização
    ok, motivo = presenca_valida(LOCAL, datetime(2026, 9, 3, tzinfo=timezone.utc), None, -23.6500, -46.6300)
    assert not ok and "janela" in motivo


def test_localizacao_invalida():
    assert not presenca_valida(LOCAL, AGORA, None, 999, -46.63)[0]
    assert not presenca_valida(LOCAL, AGORA, None, "abc", -46.63)[0]


def test_evento_sem_coordenadas_nao_aceita_localizacao():
    ok, motivo = presenca_valida(EXTRA, AGORA, None, -23.65, -46.63)
    assert not ok and "não aceita" in motivo


def test_evento_com_local_exige_codigo_ou_localizacao():
    ok, motivo = presenca_valida(LOCAL, AGORA, None)
    assert not ok and "localização" in motivo


def test_evento_aberto_sem_codigo_nem_local_aceita():
    aberto = {"inicio": EXTRA["inicio"], "fim": EXTRA["fim"]}
    assert presenca_valida(aberto, AGORA, None)[0]


def test_codigo_vale_mesmo_com_coordenadas_no_evento():
    extra = {**LOCAL, "codigo": "ABC"}
    assert presenca_valida(extra, AGORA, "ABC")[0]
    assert not presenca_valida(extra, AGORA, "XYZ")[0]
