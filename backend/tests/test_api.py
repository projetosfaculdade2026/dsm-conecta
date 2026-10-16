from datetime import datetime, timedelta, timezone

import pytest
from conftest import evento
from fastapi.testclient import TestClient

from app.api import app


class FakePool:
    def __init__(self, extra=None, rows=None, duplicada=False):
        self.extra = extra
        self.rows = rows or []
        self.duplicada = duplicada  # simula presença já gravada (RN05)
        self.executed = []

    async def fetchrow(self, sql, *args):
        if "INSERT INTO presencas" in sql:
            return None if self.duplicada else {"evento_id": args[0]}
        return None if self.extra is None else {"extra": self.extra}

    async def fetch(self, sql, *args):
        return self.rows

    async def execute(self, sql, *args):
        self.executed.append((sql, args))


class FakePub:
    def __init__(self, falha=False):
        self.msgs, self.falha = [], falha

    async def publicar(self, topic, payload):
        if self.falha:
            raise ConnectionError
        self.msgs.append((topic, payload))


@pytest.fixture
def cli():
    app.state.pool = FakePool()
    app.state.publisher = FakePub()
    return TestClient(app)  # sem "with": lifespan não roda (sem banco/broker nos testes)


def _token(c):
    r = c.post("/auth/login", json={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_health(cli):
    assert cli.get("/health").json() == {"status": "ok"}


def test_login_ok_e_falha(cli):
    assert cli.post("/auth/login", json={"username": "admin", "password": "admin123"}).status_code == 200
    assert cli.post("/auth/login", json={"username": "admin", "password": "errada"}).status_code == 401


def test_rotas_admin_exigem_token(cli):
    assert cli.get("/metrics/realtime").status_code == 401
    assert cli.delete("/content/1").status_code == 401
    assert cli.get("/export", headers={"Authorization": "Bearer lixo"}).status_code == 401


def test_admin_com_token(cli):
    assert cli.get("/metrics/realtime", headers=_token(cli)).status_code == 200
    assert cli.delete("/content/1", headers=_token(cli)).status_code == 204


def test_quiz_publico(cli):
    d = cli.get("/quiz").json()
    assert len(d["perguntas"]) == 4 and set(d["perfis"]) == {"web", "mobile", "dados", "infra"}


def test_evento_publicado_no_topico_certo(cli):
    r = cli.post("/events", json=evento())
    assert r.status_code == 202
    assert app.state.publisher.msgs[0][0] == "dsm/prod/app/interacao/tela"


def test_evento_invalido_422(cli):
    assert cli.post("/events", json=evento(schema_version=7)).status_code == 422
    assert not app.state.publisher.msgs


def test_origem_totem_rejeitada(cli):
    e = evento(origem="totem", categoria="sensor", payload={"contagem": 1})
    assert cli.post("/events", json=e).status_code == 422


def test_broker_fora_503(cli):
    app.state.publisher = FakePub(falha=True)
    assert cli.post("/events", json=evento()).status_code == 503


def _extra(ini, fim, codigo="DSM"):
    return {"inicio": ini.isoformat(), "fim": fim.isoformat(), "codigo": codigo}


def test_presenca_valida_e_remove_codigo(cli):
    agora = datetime.now(timezone.utc)
    app.state.pool = FakePool(_extra(agora - timedelta(hours=1), agora + timedelta(hours=1)))
    e = evento(categoria="presenca", payload={"evento_id": 1, "codigo": "DSM"})
    assert cli.post("/events", json=e).status_code == 202
    assert "DSM" not in app.state.publisher.msgs[0][1]


def test_presenca_fora_da_janela_409(cli):
    agora = datetime.now(timezone.utc)
    app.state.pool = FakePool(_extra(agora - timedelta(days=2), agora - timedelta(days=1)))
    e = evento(categoria="presenca", payload={"evento_id": 1, "codigo": "DSM"})
    assert cli.post("/events", json=e).status_code == 409


def test_presenca_evento_inexistente_404(cli):
    e = evento(categoria="presenca", payload={"evento_id": 1})
    assert cli.post("/events", json=e).status_code == 404


def test_excluir_sessao(cli):
    assert cli.delete("/sessions/sessao-abc12345").status_code == 204
    assert "DELETE FROM telemetria" in app.state.pool.executed[0][0]


def test_mensagem_vazia_422(cli):
    assert cli.post("/messages", json={"nome": "x", "texto": "  "}).status_code == 422


# ---------------------------------------------------------------- RN05, RF11/RN04, RF20, RNF03, devolutiva
def _extra_local(agora, codigo=None):
    e = {"inicio": (agora - timedelta(hours=1)).isoformat(), "fim": (agora + timedelta(hours=1)).isoformat(),
         "lat": -23.7617, "lon": -46.6987}
    if codigo:
        e["codigo"] = codigo
    return e


def test_presenca_repetida_na_mesma_sessao_409(cli):  # RN05 no servidor
    agora = datetime.now(timezone.utc)
    app.state.pool = FakePool(_extra(agora - timedelta(hours=1), agora + timedelta(hours=1)), duplicada=True)
    e = evento(categoria="presenca", payload={"evento_id": 1, "codigo": "DSM"})
    r = cli.post("/events", json=e)
    assert r.status_code == 409 and "já registrada" in r.json()["detail"]
    assert not app.state.publisher.msgs


def test_presenca_por_localizacao_dentro_do_raio(cli):  # RF11 / RN04
    agora = datetime.now(timezone.utc)
    app.state.pool = FakePool(_extra_local(agora))
    e = evento(categoria="presenca", payload={"evento_id": 1, "lat": -23.7618, "lon": -46.6987})
    assert cli.post("/events", json=e).status_code == 202
    msg = app.state.publisher.msgs[0][1]
    assert "-23.76" not in msg and '"metodo":"localizacao"' in msg  # posição exata não vai para o broker


def test_presenca_por_localizacao_longe_409(cli):
    agora = datetime.now(timezone.utc)
    app.state.pool = FakePool(_extra_local(agora))
    e = evento(categoria="presenca", payload={"evento_id": 1, "lat": -23.80, "lon": -46.70})
    r = cli.post("/events", json=e)
    assert r.status_code == 409 and "raio" in r.json()["detail"]
    assert not app.state.publisher.msgs


def test_presenca_desfeita_se_broker_falha(cli):
    agora = datetime.now(timezone.utc)
    app.state.pool = FakePool(_extra(agora - timedelta(hours=1), agora + timedelta(hours=1)))
    app.state.publisher = FakePub(falha=True)
    e = evento(categoria="presenca", payload={"evento_id": 1, "codigo": "DSM"})
    assert cli.post("/events", json=e).status_code == 503
    assert any("DELETE FROM presencas" in sql for sql, _ in app.state.pool.executed)  # permite nova tentativa


def test_excluir_sessao_remove_presencas(cli):
    cli.delete("/sessions/sessao-abc12345")
    assert any("DELETE FROM presencas" in sql for sql, _ in app.state.pool.executed)


def test_config_janela_exige_token(cli):
    assert cli.get("/admin/config").status_code == 401
    assert cli.put("/admin/config", json={"janela_s": 30}).status_code == 401


def test_config_janela_altera_e_valida(cli):
    h = _token(cli)
    assert cli.put("/admin/config", json={"janela_s": 300}, headers=h).json()["janela_s"] == 300
    assert cli.get("/admin/config", headers=h).json()["janela_s"] == 300
    assert cli.get("/metrics/realtime", headers=h).json()["janela_s"] == 300
    assert cli.put("/admin/config", json={"janela_s": 5}, headers=h).status_code == 422
    assert cli.put("/admin/config", json={"janela_s": 99999}, headers=h).status_code == 422
    cli.put("/admin/config", json={"janela_s": 60}, headers=h)


def test_dados_abertos_publicos_aplicam_rn08(cli):
    from datetime import datetime as dt
    h = dt(2026, 10, 1, 14, tzinfo=timezone.utc)
    app.state.pool = FakePool(rows=[
        {"bucket": h, "categoria": "interacao", "total": 25},
        {"bucket": h, "categoria": "quiz", "total": 4},         # < 10: não publica
        {"bucket": h, "categoria": "presenca", "total": 50},    # categoria não publicável
    ])
    r = cli.get("/open-data/telemetria")  # sem token
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert r.text.splitlines() == ["hora,categoria,total", "2026-10-01T14:00:00+00:00,interacao,25"]
    assert cli.get("/open-data/telemetria?format=json").json() == [
        {"hora": "2026-10-01T14:00:00+00:00", "categoria": "interacao", "total": 25}]


def test_dicionario_de_dados_publico(cli):
    d = cli.get("/open-data/dicionario").json()
    assert [c["nome"] for c in d["campos"]] == ["hora", "categoria", "total"]


def test_relatorio_escola_exige_token_e_mascara(cli):
    assert cli.get("/admin/report").status_code == 401
    app.state.pool = FakePool(rows=[{"k": "inicio", "n": 12}, {"k": "curso", "n": 3}])
    r = cli.get("/admin/report", headers=_token(cli))
    assert r.status_code == 200 and "| inicio | 12 |" in r.text and "| curso |" not in r.text
