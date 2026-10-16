from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.api import app

ROW = {"id": 1, "kind": "evento", "title": "Feira", "body": "b", "approved": True,
       "extra": '{"inicio":"x","fim":"y","codigo":"SEGREDO"}'}


class Pool:
    def __init__(self):
        self.sql = []

    async def fetchrow(self, sql, *a):
        self.sql.append(sql)
        return ROW

    async def fetch(self, sql, *a):
        self.sql.append(sql)
        if "FROM content" in sql:
            return [ROW]
        if "telemetria_hora" in sql:
            return [{"bucket": datetime(2026, 9, 1, tzinfo=timezone.utc), "categoria": "interacao", "total": 12}]
        if "FROM mensagens" in sql:
            return [{"nome": "a", "texto": "oi", "criado_em": datetime(2026, 9, 1, tzinfo=timezone.utc)}]
        if "session_id" in sql:
            return [{"ts": datetime(2026, 9, 1, tzinfo=timezone.utc), "categoria": "quiz", "payload": '{"questao":1}'}]
        if "GROUP BY 1,2" in sql:
            return [{"dia": "2026-09-01", "categoria": "interacao", "total": 12}, {"dia": "2026-09-01", "categoria": "quiz", "total": 3}]
        return [{"tela": "inicio", "perfil": "web", "categoria": "x", "total": 11}]

    async def execute(self, sql, *a):
        self.sql.append(sql)


@pytest.fixture
def cli():
    app.state.pool = Pool()
    c = TestClient(app)
    tok = c.post("/auth/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {tok}"
    return c


def test_listagem_publica_esconde_codigo(cli):
    c = TestClient(app)  # sem token
    assert "codigo" not in c.get("/content").json()[0]["extra"]


def test_admin_ve_codigo(cli):
    assert cli.get("/admin/content").json()[0]["extra"]["codigo"] == "SEGREDO"


def test_crud_conteudo(cli):
    corpo = {"kind": "faq", "title": "t", "body": "b", "extra": {}}
    assert cli.post("/content", json=corpo).status_code == 201
    assert cli.put("/content/1", json=corpo).status_code == 200
    assert cli.post("/content", json={**corpo, "kind": "invalido"}).status_code == 422


def test_metricas_publicas_aplicam_minimo(cli):
    d = TestClient(app).get("/metrics/public").json()
    assert d["min_grupo"] == 10
    assert all(x["total"] >= 10 for x in d["diario"]) and len(d["diario"]) == 1  # grupo com 3 foi mascarado


def test_export_csv_e_json(cli):
    csv_ = cli.get("/export?format=csv")
    assert csv_.text.splitlines()[0] == "hora,categoria,total" and "interacao" in csv_.text
    assert cli.get("/export?format=json").json()[0]["total"] == 12


def test_historico_resumo_mensagens(cli):
    assert cli.get("/sessions/sessao-abc12345/history").json()[0]["payload"] == {"questao": 1}
    assert cli.get("/metrics/summary").status_code == 200
    assert cli.get("/admin/messages").json()[0]["texto"] == "oi"
    assert cli.post("/messages", json={"nome": "a", "texto": "ola"}).status_code == 201


def test_websocket_exige_token(cli):
    c = TestClient(app)
    with pytest.raises(Exception):  # fechamento 4401 sem token
        with c.websocket_connect("/ws/live"):
            pass
    tok = cli.headers["Authorization"].split()[1]
    with c.websocket_connect(f"/ws/live?token={tok}") as ws:
        assert ws is not None
