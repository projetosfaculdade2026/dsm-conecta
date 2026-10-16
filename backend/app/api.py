"""Interface de programação (FastAPI): conteúdo, eventos, métricas e canal em tempo real."""
import asyncio
import csv
import io
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal

import aiomqtt
from fastapi import Depends, FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .analytics import JANELA_MAX, JANELA_MIN, Engine
from .auth import create_token, credenciais_ok, decode_token, require_admin
from .config import settings
from .db import create_pool
from .dedup import Dedup
from .opendata import DICIONARIO, para_csv, preparar_publicacao, relatorio_escola
from .rules import MIN_GRUPO, mascarar_grupo, presenca_valida
from .schema import Evento, parse_message, topic_for

QUIZ = {
    "perguntas": [
        {"id": 1, "texto": "O que mais te empolga em tecnologia?", "opcoes": [
            {"texto": "Ver um site ganhar vida", "perfil": "web"},
            {"texto": "Criar um app para o celular", "perfil": "mobile"},
            {"texto": "Descobrir padrões em dados", "perfil": "dados"},
            {"texto": "Fazer sistemas grandes funcionarem", "perfil": "infra"}]},
        {"id": 2, "texto": "Em um projeto em grupo, você prefere...", "opcoes": [
            {"texto": "Cuidar da aparência e da experiência", "perfil": "web"},
            {"texto": "Fazer rodar em vários aparelhos", "perfil": "mobile"},
            {"texto": "Analisar números e resultados", "perfil": "dados"},
            {"texto": "Garantir que nada saia do ar", "perfil": "infra"}]},
        {"id": 3, "texto": "Qual desafio você toparia?", "opcoes": [
            {"texto": "Deixar um site lindo e rápido", "perfil": "web"},
            {"texto": "Publicar um app que todos usam", "perfil": "mobile"},
            {"texto": "Prever o futuro com dados", "perfil": "dados"},
            {"texto": "Atender milhares de pessoas ao mesmo tempo", "perfil": "infra"}]},
        {"id": 4, "texto": "Seu superpoder seria...", "opcoes": [
            {"texto": "Criatividade", "perfil": "web"},
            {"texto": "Praticidade", "perfil": "mobile"},
            {"texto": "Curiosidade", "perfil": "dados"},
            {"texto": "Organização", "perfil": "infra"}]},
    ],
    "perfis": {
        "web": {"titulo": "Web e experiência do usuário", "descricao": "Você gosta de criar interfaces que as pessoas usam no navegador."},
        "mobile": {"titulo": "Aplicativos multiplataforma", "descricao": "Você gosta de criar um app que roda em celular, web e desktop."},
        "dados": {"titulo": "Dados e análise", "descricao": "Você gosta de transformar dados em decisões."},
        "infra": {"titulo": "Sistemas distribuídos e infraestrutura", "descricao": "Você gosta de fazer sistemas grandes serem rápidos e confiáveis."},
    },
}


def log(evento: str, **kw) -> None:
    print(json.dumps({"evento": evento, **kw}, default=str), flush=True)


def _json(v):
    return json.loads(v) if isinstance(v, str) else v


class Hub:
    def __init__(self):
        self.clients: set[WebSocket] = set()

    async def broadcast(self, msg: dict) -> None:
        for ws in list(self.clients):
            try:
                await ws.send_json(msg)
            except Exception:  # noqa: BLE001
                self.clients.discard(ws)


class Publisher:
    """Gateway HTTP -> MQTT: o app publica via API, que publica no broker (QoS 1)."""

    def __init__(self):
        self.client = None
        self.lock = asyncio.Lock()

    async def publicar(self, topic: str, payload: str) -> None:
        async with self.lock:
            for _ in range(2):
                try:
                    if self.client is None:
                        c = aiomqtt.Client(hostname=settings.mqtt_host, port=settings.mqtt_port,
                                           username=settings.mqtt_user, password=settings.mqtt_pass,
                                           identifier=f"dsm-api-pub-{os.getpid()}")
                        await c.__aenter__()
                        self.client = c
                    await self.client.publish(topic, payload, qos=1)
                    return
                except aiomqtt.MqttError:
                    self.client = None
            raise ConnectionError("broker indisponível")

    async def close(self):
        if self.client is not None:
            await self.client.__aexit__(None, None, None)


async def live_consumer(app: FastAPI) -> None:
    dedup = Dedup(50_000)
    while True:
        try:
            async with aiomqtt.Client(hostname=settings.mqtt_host, port=settings.mqtt_port,
                                      username=settings.mqtt_user, password=settings.mqtt_pass,
                                      identifier=f"dsm-api-live-{os.getpid()}") as c:
                await c.subscribe("dsm/+/+/+/+", qos=1)
                async for m in c.messages:
                    partes = str(m.topic).split("/")
                    if partes[3] == "status":
                        app.state.totem = bytes(m.payload).decode() if m.payload else "desconhecido"
                        continue
                    try:
                        ev = parse_message(m.payload)
                    except (ValueError, TypeError):
                        continue
                    if not dedup.visto(str(ev.event_id)):
                        app.state.engine.ingest(ev)
        except aiomqtt.MqttError as e:
            log("live_mqtt_erro", erro=str(e))
            await asyncio.sleep(2)


async def ticker(app: FastAPI) -> None:
    while True:
        await asyncio.sleep(0.5)
        if app.state.hub.clients:
            snap = app.state.engine.snapshot()
            snap["totem"] = app.state.totem
            await app.state.hub.broadcast(snap)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await create_pool()
    app.state.publisher = Publisher()
    tasks = [asyncio.create_task(live_consumer(app)), asyncio.create_task(ticker(app))]
    yield
    for t in tasks:
        t.cancel()
    await app.state.publisher.close()
    await app.state.pool.close()


app = FastAPI(title="DSM Conecta API", version="1.0.0", lifespan=lifespan,
              description="Conteúdo, telemetria, métricas e tempo real do projeto DSM Conecta.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.state.engine = Engine()
app.state.hub = Hub()
app.state.totem = "desconhecido"


# ---------------------------------------------------------------- público
@app.get("/health")
async def health():
    return {"status": "ok"}


class Login(BaseModel):
    username: str
    password: str


@app.post("/auth/login")
async def login(body: Login):
    if not credenciais_ok(body.username, body.password):
        raise HTTPException(401, "credenciais inválidas")
    return {"access_token": create_token(body.username), "token_type": "bearer"}


def _row(r, publico: bool) -> dict:
    extra = dict(_json(r["extra"]))
    if publico:
        extra.pop("codigo", None)  # o código do QR nunca sai na listagem pública
    return {"id": r["id"], "kind": r["kind"], "title": r["title"], "body": r["body"],
            "extra": extra, "approved": r["approved"]}


@app.get("/content")
async def listar_conteudo(request: Request, kind: str | None = None):
    rows = await request.app.state.pool.fetch(
        "SELECT id, kind, title, body, extra, approved FROM content "
        "WHERE approved AND ($1::text IS NULL OR kind=$1) ORDER BY id", kind)
    return [_row(r, True) for r in rows]


@app.get("/quiz")
async def quiz():
    return QUIZ


class Mensagem(BaseModel):
    nome: str = ""
    texto: str


@app.post("/messages", status_code=201)
async def enviar_mensagem(m: Mensagem, request: Request):
    if not m.texto.strip() or len(m.texto) > 1000:
        raise HTTPException(422, "texto inválido")
    await request.app.state.pool.execute("INSERT INTO mensagens(nome, texto) VALUES($1,$2)", m.nome[:80], m.texto)
    return {"status": "recebida"}


@app.post("/events", status_code=202)
async def receber_evento(ev: Evento, request: Request):
    if ev.origem != "app":
        raise HTTPException(422, "este endpoint aceita apenas origem 'app'")
    pool = request.app.state.pool
    presenca = None  # (evento_id, session_id) gravado para a RN05; desfeito se o broker falhar
    if ev.categoria == "presenca":
        try:
            evento_id = int(ev.payload["evento_id"])
        except (TypeError, ValueError) as e:
            raise HTTPException(422, "evento_id inválido") from e
        row = await pool.fetchrow("SELECT extra FROM content WHERE kind='evento' AND approved AND id=$1", evento_id)
        if row is None:
            raise HTTPException(404, "evento não encontrado")
        p = ev.payload
        ok, motivo = presenca_valida(_json(row["extra"]), datetime.now(timezone.utc),
                                     p.get("codigo"), p.get("lat"), p.get("lon"))
        if not ok:
            raise HTTPException(409, motivo)  # RN03 / RN04 / código inválido
        metodo = "codigo" if p.get("codigo") else "localizacao"
        nova = await pool.fetchrow(
            "INSERT INTO presencas(evento_id, session_id, metodo) VALUES($1,$2,$3) "
            "ON CONFLICT DO NOTHING RETURNING evento_id", evento_id, ev.session_id, metodo)
        if nova is None:
            raise HTTPException(409, "presença já registrada para esta sessão neste evento")  # RN05
        presenca = (evento_id, ev.session_id)
        for campo in ("codigo", "lat", "lon"):  # nem o código secreto nem a posição exata seguem para o broker
            p.pop(campo, None)
        p["metodo"] = metodo
    try:
        await request.app.state.publisher.publicar(topic_for(ev, settings.ambiente), ev.model_dump_json())
    except ConnectionError as e:
        if presenca:  # nada foi publicado: libera nova tentativa do visitante
            await pool.execute("DELETE FROM presencas WHERE evento_id=$1 AND session_id=$2", *presenca)
        raise HTTPException(503, "broker indisponível") from e
    return {"status": "aceito", "event_id": str(ev.event_id)}


@app.get("/sessions/{sid}/history")
async def historico(sid: str, request: Request):  # RF12
    rows = await request.app.state.pool.fetch(
        "SELECT ts, categoria, payload FROM telemetria WHERE session_id=$1 ORDER BY ts DESC LIMIT 100", sid)
    return [{"ts": r["ts"].isoformat(), "categoria": r["categoria"], "payload": _json(r["payload"])} for r in rows]


@app.delete("/sessions/{sid}", status_code=204)
async def excluir_sessao(sid: str, request: Request):  # RF12 / RN02
    await request.app.state.pool.execute("DELETE FROM telemetria WHERE session_id=$1", sid)
    await request.app.state.pool.execute("DELETE FROM presencas WHERE session_id=$1", sid)
    return Response(status_code=204)


@app.get("/metrics/public")
async def metricas_publicas(request: Request):
    """RNF16/RN08: somente agregados com no mínimo MIN_GRUPO registros por grupo."""
    p = request.app.state.pool
    telas = await p.fetch(
        "SELECT payload->>'tela' AS tela, count(*)::int AS total FROM telemetria "
        "WHERE categoria='interacao' AND ts > now() - interval '7 days' GROUP BY 1 "
        "HAVING count(*) >= $1 ORDER BY 2 DESC LIMIT 10", MIN_GRUPO)
    perfis = await p.fetch(
        "SELECT payload->>'perfil' AS perfil, count(*)::int AS total FROM telemetria "
        "WHERE categoria='quiz' GROUP BY 1 HAVING count(*) >= $1 ORDER BY 2 DESC", MIN_GRUPO)
    diario = await p.fetch(
        "SELECT to_char(date_trunc('day', ts), 'YYYY-MM-DD') AS dia, categoria, count(*)::int AS total "
        "FROM telemetria WHERE ts > now() - interval '30 days' GROUP BY 1,2 ORDER BY 1 DESC")
    return {"min_grupo": MIN_GRUPO, "telas": [dict(r) for r in telas], "perfis": [dict(r) for r in perfis],
            "diario": mascarar_grupo([dict(r) for r in diario])}


async def _agregado_publico(pool) -> list[dict]:
    rows = await pool.fetch(
        "SELECT bucket, categoria, total::int AS total FROM telemetria_hora ORDER BY bucket DESC LIMIT 5000")
    return preparar_publicacao(
        [{"hora": r["bucket"].isoformat(), "categoria": r["categoria"], "total": r["total"]} for r in rows])


@app.get("/open-data/telemetria")
async def dados_abertos(request: Request, format: Literal["csv", "json"] = "csv"):
    """RNF03 / RN08: dados abertos, sem autenticação, só agregados com no mínimo 10 registros por grupo."""
    dados = await _agregado_publico(request.app.state.pool)
    if format == "json":
        return dados
    return Response(para_csv(dados), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=telemetria_agregada.csv"})


@app.get("/open-data/dicionario")
async def dicionario_de_dados():
    """RNF03: dicionário de dados do conjunto aberto."""
    return DICIONARIO


# ---------------------------------------------------------------- administrativo
class ConteudoIn(BaseModel):
    kind: Literal["apresentacao", "disciplina", "projeto", "depoimento", "evento", "faq"]
    title: str
    body: str = ""
    extra: dict = {}
    approved: bool = True


@app.get("/admin/content")
async def listar_admin(request: Request, _: str = Depends(require_admin)):
    rows = await request.app.state.pool.fetch("SELECT id, kind, title, body, extra, approved FROM content ORDER BY id")
    return [_row(r, False) for r in rows]


@app.post("/content", status_code=201)
async def criar_conteudo(c: ConteudoIn, request: Request, _: str = Depends(require_admin)):
    r = await request.app.state.pool.fetchrow(
        "INSERT INTO content(kind,title,body,extra,approved) VALUES($1,$2,$3,$4::jsonb,$5) "
        "RETURNING id, kind, title, body, extra, approved", c.kind, c.title, c.body, json.dumps(c.extra), c.approved)
    return _row(r, False)


@app.put("/content/{cid}")
async def alterar_conteudo(cid: int, c: ConteudoIn, request: Request, _: str = Depends(require_admin)):
    r = await request.app.state.pool.fetchrow(
        "UPDATE content SET kind=$2,title=$3,body=$4,extra=$5::jsonb,approved=$6 WHERE id=$1 "
        "RETURNING id, kind, title, body, extra, approved", cid, c.kind, c.title, c.body, json.dumps(c.extra), c.approved)
    if r is None:
        raise HTTPException(404, "conteúdo não encontrado")
    return _row(r, False)


@app.delete("/content/{cid}", status_code=204)
async def remover_conteudo(cid: int, request: Request, _: str = Depends(require_admin)):
    await request.app.state.pool.execute("DELETE FROM content WHERE id=$1", cid)
    return Response(status_code=204)


@app.get("/admin/messages")
async def mensagens(request: Request, _: str = Depends(require_admin)):
    rows = await request.app.state.pool.fetch("SELECT nome, texto, criado_em FROM mensagens ORDER BY criado_em DESC LIMIT 100")
    return [{"nome": r["nome"], "texto": r["texto"], "criado_em": r["criado_em"].isoformat()} for r in rows]


class Config(BaseModel):
    janela_s: int = Field(ge=JANELA_MIN, le=JANELA_MAX)


def _config(request: Request) -> dict:
    return {"janela_s": request.app.state.engine.janela, "janela_min": JANELA_MIN, "janela_max": JANELA_MAX}


@app.get("/admin/config")
async def ler_config(request: Request, _: str = Depends(require_admin)):
    return _config(request)


@app.put("/admin/config")
async def alterar_config(c: Config, request: Request, _: str = Depends(require_admin)):  # RF20
    request.app.state.engine.set_janela(c.janela_s)
    return _config(request)


@app.get("/admin/report")
async def relatorio(request: Request, _: str = Depends(require_admin)):
    """Devolutiva agregada para a escola parceira (Documento de Visão, seção 9)."""
    p = request.app.state.pool
    telas = await p.fetch("SELECT payload->>'tela' AS k, count(*)::int AS n FROM telemetria "
                          "WHERE categoria='interacao' GROUP BY 1 ORDER BY 2 DESC LIMIT 10")
    perfis = await p.fetch("SELECT payload->>'perfil' AS k, count(*)::int AS n FROM telemetria "
                           "WHERE categoria='quiz' GROUP BY 1 ORDER BY 2 DESC")
    pres = await p.fetch("SELECT c.title AS k, count(*)::int AS n FROM presencas x JOIN content c ON c.id = x.evento_id "
                         "GROUP BY 1 ORDER BY 2 DESC")
    texto = relatorio_escola([(r["k"], r["n"]) for r in telas if r["k"]],
                             [(r["k"], r["n"]) for r in perfis if r["k"]],
                             [(r["k"], r["n"]) for r in pres])
    return Response(texto, media_type="text/markdown; charset=utf-8")


@app.get("/metrics/realtime")
async def tempo_real(request: Request, _: str = Depends(require_admin)):
    snap = request.app.state.engine.snapshot()
    snap["totem"] = request.app.state.totem
    return snap


@app.get("/metrics/summary")
async def resumo(request: Request, _: str = Depends(require_admin)):
    rows = await request.app.state.pool.fetch(
        "SELECT categoria, count(*)::int AS total FROM telemetria WHERE ts > now() - interval '24 hours' GROUP BY 1")
    return {"ultimas_24h": {r["categoria"]: r["total"] for r in rows}}


@app.get("/export")
async def exportar(request: Request, format: Literal["csv", "json"] = "csv", _: str = Depends(require_admin)):  # RF24
    rows = await request.app.state.pool.fetch(
        "SELECT bucket, categoria, total::int AS total FROM telemetria_hora ORDER BY bucket DESC LIMIT 5000")
    dados = [{"hora": r["bucket"].isoformat(), "categoria": r["categoria"], "total": r["total"]} for r in rows]
    if format == "json":
        return dados
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["hora", "categoria", "total"])
    w.writeheader()
    w.writerows(dados)
    return Response(buf.getvalue(), media_type="text/csv")


@app.websocket("/ws/live")
async def ws_live(ws: WebSocket, token: str = ""):
    try:
        decode_token(token)
    except HTTPException:
        await ws.close(code=4401)
        return
    await ws.accept()
    app.state.hub.clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        app.state.hub.clients.discard(ws)


# Simulador do nó sensor no navegador (Documento de Visão, 6.5): http://localhost:8000/simulador/
SIM_DIR = os.environ.get("SIM_DIR", "/srv/simulador")
if os.path.isdir(SIM_DIR):
    app.mount("/simulador", StaticFiles(directory=SIM_DIR, html=True), name="simulador")

# Cliente web (estático) servido na raiz; registrado por último para não sombrear as rotas da API.
WEB_DIR = os.environ.get("WEB_DIR", "/srv/web")
if os.path.isdir(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
