import json

import pytest
from conftest import evento

from app.schema import Evento, parse_message, topic_for, topic_ok


def test_evento_valido():
    ev = parse_message(json.dumps(evento()))
    assert ev.categoria == "interacao"


def test_json_malformado():
    with pytest.raises(ValueError):
        parse_message(b"{nao e json")


def test_payload_none():
    with pytest.raises(ValueError):
        parse_message(None)


@pytest.mark.parametrize("campo", ["event_id", "session_id", "categoria", "origem", "ts", "schema_version", "payload"])
def test_campo_obrigatorio(campo):
    e = evento()
    del e[campo]
    with pytest.raises(ValueError):
        parse_message(json.dumps(e))


def test_versao_nao_suportada():
    with pytest.raises(ValueError):
        parse_message(json.dumps(evento(schema_version=99)))


def test_ts_sem_fuso():
    with pytest.raises(ValueError):
        parse_message(json.dumps(evento(ts="2026-09-01T10:00:00")))


def test_combinacao_invalida():
    with pytest.raises(ValueError):
        parse_message(json.dumps(evento(origem="totem", categoria="quiz", payload={"questao": 1, "perfil": "web"})))


def test_payload_sem_campos_obrigatorios():
    with pytest.raises(ValueError):
        parse_message(json.dumps(evento(payload={})))


def test_totem_contagem_valida_e_invalida():
    ok = evento(origem="totem", categoria="sensor", payload={"contagem": 3})
    assert parse_message(json.dumps(ok)).payload["contagem"] == 3
    for ruim in (-1, "x", True):
        with pytest.raises(ValueError):
            parse_message(json.dumps(evento(origem="totem", categoria="sensor", payload={"contagem": ruim})))


def test_sensor_app_exige_tipo_valor():
    with pytest.raises(ValueError):
        parse_message(json.dumps(evento(categoria="sensor", payload={"tipo": "acelerometro"})))
    assert parse_message(json.dumps(evento(categoria="sensor", payload={"tipo": "a", "valor": 1.0})))


def test_topicos():
    ev = Evento(**evento())
    assert topic_for(ev) == "dsm/prod/app/interacao/tela"
    assert topic_ok("dsm/prod/app/interacao/tela", ev)
    assert not topic_ok("dsm/prod/totem/interacao/tela", ev)
    assert not topic_ok("dsm/prod/app/interacao", ev)
