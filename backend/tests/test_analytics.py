import pytest
from conftest import evento

from app.analytics import Engine, SlidingWindow, is_anomaly, moving_average, zscore
from app.schema import Evento


def test_janela_descarta_antigos():
    w = SlidingWindow(10)
    w.add("a", t=0); w.add("b", t=5); w.add("c", t=9)
    assert w.items(now=10) == ["b", "c"]  # "a" (t=0) saiu da janela
    assert w.items(now=20) == []


def test_media_movel():
    assert moving_average([1, 2, 3, 4], 2) == [1, 1.5, 2.5, 3.5]
    with pytest.raises(ValueError):
        moving_average([1], 0)


def test_zscore_e_anomalia():
    h = [10, 11, 9, 10, 10, 11]
    assert zscore(h, 10) == pytest.approx(0, abs=0.5)
    assert is_anomaly(h, 40) is True
    assert is_anomaly(h, 11) is False


def test_anomalia_exige_amostras_minimas():
    assert is_anomaly([1, 1], 100) is False


def test_serie_constante_nao_gera_falso_positivo():
    assert is_anomaly([5] * 10, 5) is False


def _ev(cat="interacao", sessao="sessao-abc12345", **payload):
    p = payload or {"tela": "inicio"}
    return Evento(**evento(categoria=cat, session_id=sessao, payload=p))


def test_engine_ranking_e_ativos():
    e = Engine(window=60)
    for i in range(3):
        e.ingest(_ev(tela="quiz", sessao=f"sessao-{i}0000000"), now=100)
    e.ingest(_ev(tela="inicio"), now=101)
    assert e.ranking(now=102)[0] == {"tela": "quiz", "total": 3}
    assert e.visitantes_ativos(now=102) == 4
    assert e.visitantes_ativos(now=500) == 0  # fora da janela


def test_engine_presenca_unica_por_sessao():
    e = Engine()
    for _ in range(3):
        e.ingest(_ev("presenca", evento_id=1), now=1)
    assert e.snapshot(now=2)["presencas"] == {"1": 1}  # RN05


def test_engine_quiz():
    e = Engine()
    e.ingest(_ev("quiz", questao=1, perfil="web"), now=1)
    assert e.snapshot(now=2)["quiz"] == {"web": 1}


def test_engine_detecta_pico():
    e = Engine(bucket=5, hist=12)
    base = 10_000
    for b in range(2, 14):  # histórico estável: 2 eventos por bucket
        for _ in range(2):
            e.ingest(_ev(), now=base + b * 5 - 100)
    normal = e.alerta(now=base - 100 + 14 * 5)
    assert normal["anomalia"] is False
    cur_bucket = int((base - 100 + 14 * 5) // 5)
    e.buckets[cur_bucket - 1] = 60  # pico no último bucket concluído
    assert e.alerta(now=base - 100 + 14 * 5)["anomalia"] is True


def test_snapshot_formato():
    s = Engine().snapshot(now=1000)
    assert {"visitantes_ativos", "ranking", "serie", "media_movel", "alerta"} <= s.keys()
    assert len(s["serie"]) == 12


def test_janela_configuravel_filtra_ranking_e_ativos():  # RF20
    e = Engine(window=60)
    e.ingest(_ev(tela="antigo", sessao="sessao-antiga01"), now=100)
    e.ingest(_ev(tela="novo", sessao="sessao-nova0001"), now=190)
    assert e.visitantes_ativos(now=200) == 1 and e.ranking(now=200) == [{"tela": "novo", "total": 1}]  # padrão 60 s
    e.set_janela(300)
    assert e.visitantes_ativos(now=200) == 2 and len(e.ranking(now=200)) == 2
    e.set_janela(30)
    assert e.visitantes_ativos(now=200) == 1 and e.ranking(now=200) == [{"tela": "novo", "total": 1}]
    assert e.snapshot(now=200)["janela_s"] == 30


def test_ampliar_janela_recupera_eventos_ja_fora_da_janela_anterior():
    e = Engine(window=10)
    e.ingest(_ev(), now=100)
    assert e.visitantes_ativos(now=200) == 0
    e.set_janela(300)
    assert e.visitantes_ativos(now=200) == 1


@pytest.mark.parametrize("v", [0, 9, 3601, -5, 60.5, "60", True, None])
def test_janela_invalida_rejeitada(v):
    with pytest.raises(ValueError):
        Engine().set_janela(v)


def test_janela_nos_limites():
    e = Engine()
    e.set_janela(10)
    e.set_janela(3600)
    assert e.janela == 3600
