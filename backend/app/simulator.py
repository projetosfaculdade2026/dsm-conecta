"""Nó sensor simulado (totem) e gerador de carga sintética.

  python -m app.simulator totem --intervalo 3
  python -m app.simulator carga --taxa 50 --total 5000 --sessoes 1000
  python -m app.simulator carga --taxa 50 --total 5000 --conexoes 1000   # 1000 conexões MQTT reais (RNF06)
"""
import argparse
import asyncio
import contextlib
import json
import random
import time
import uuid
from datetime import datetime, timezone

import aiomqtt
import asyncpg

from .config import settings

TELAS = ["inicio", "curso", "eventos", "quiz", "painel", "projetos"]
STATUS = "dsm/prod/totem/status/sensor-01"


def novo_evento(origem, categoria, payload, sessao):
    return {"event_id": str(uuid.uuid4()), "session_id": sessao, "categoria": categoria, "origem": origem,
            "ts": datetime.now(timezone.utc).isoformat(), "schema_version": 1, "payload": payload}


def cliente(ident, will=None):
    return aiomqtt.Client(hostname=settings.mqtt_host, port=settings.mqtt_port, username=settings.mqtt_user,
                          password=settings.mqtt_pass, identifier=ident, will=will)


async def totem(intervalo: float):
    # Última vontade + retenção: o broker publica "offline" se o totem cair.
    will = aiomqtt.Will(topic=STATUS, payload="offline", qos=1, retain=True)
    while True:
        try:
            async with cliente("dsm-totem-01", will) as c:
                await c.publish(STATUS, "online", qos=1, retain=True)
                print("totem online", flush=True)
                while True:
                    ev = novo_evento("totem", "sensor", {"contagem": random.randint(0, 25), "local": "estande"}, "totem-sensor-01")
                    await c.publish("dsm/prod/totem/sensor/contagem", json.dumps(ev), qos=1)
                    await asyncio.sleep(intervalo)
        except aiomqtt.MqttError as e:
            print("erro mqtt:", e, flush=True)
            await asyncio.sleep(2)


def _gerar(sessoes, lote):
    s = random.choice(sessoes)
    r = random.random()
    if r < 0.7:
        return "dsm/prod/app/interacao/tela", novo_evento("app", "interacao", {"tela": random.choice(TELAS), "lote": lote}, s)
    if r < 0.9:
        return "dsm/prod/app/quiz/resposta", novo_evento("app", "quiz", {"questao": random.randint(1, 4), "perfil": random.choice(["web", "mobile", "dados", "infra"]), "lote": lote}, s)
    return "dsm/prod/app/sensor/dispositivo", novo_evento("app", "sensor", {"tipo": "acelerometro", "valor": round(random.uniform(9, 11), 2), "lote": lote}, s)


async def _conectados_segundo_broker(timeout: float = 15.0):
    """Lê do próprio broker quantos clientes estão conectados ($SYS atualiza a cada ~10 s)."""
    try:
        async with cliente("dsm-carga-sys") as c:
            await c.subscribe("$SYS/broker/clients/connected")
            async with asyncio.timeout(timeout):
                async for m in c.messages:
                    return int(bytes(m.payload).decode())
    except (aiomqtt.MqttError, TimeoutError, ValueError):
        return None


async def carga(taxa: int, total: int, nsessoes: int, conexoes: int = 1):
    """Ensaio de carga em QoS 1. Com `conexoes` > 1, abre essa quantidade de conexões MQTT reais e simultâneas."""
    lote = uuid.uuid4().hex[:8]
    sessoes = [uuid.uuid4().hex for _ in range(max(nsessoes, conexoes))]
    enviadas = 0
    async with contextlib.AsyncExitStack() as pilha:
        clientes = []
        for ini in range(0, conexoes, 100):  # abre em blocos de 100 para não sobrecarregar o broker
            bloco = range(ini, min(ini + 100, conexoes))
            clientes += await asyncio.gather(*[pilha.enter_async_context(cliente(f"dsm-carga-{lote}-{i}")) for i in bloco])
        print(f"{len(clientes)} conexão(ões) MQTT aberta(s)", flush=True)
        sys_task = asyncio.create_task(_conectados_segundo_broker()) if conexoes > 1 else None
        while enviadas < total:
            t0 = time.monotonic()
            n = min(taxa, total - enviadas)
            msgs = [_gerar(sessoes, lote) for _ in range(n)]
            await asyncio.gather(*[clientes[(enviadas + i) % len(clientes)].publish(t, json.dumps(e), qos=1)
                                   for i, (t, e) in enumerate(msgs)])
            enviadas += n
            await asyncio.sleep(max(0, 1 - (time.monotonic() - t0)))
        reportado = await sys_task if sys_task else None
    print(f"lote {lote}: enviadas {enviadas}; aguardando gravação...", flush=True)
    await asyncio.sleep(5)
    db = await asyncpg.connect(settings.database_url)
    gravadas = await db.fetchval("SELECT count(*) FROM telemetria WHERE payload->>'lote' = $1", lote)
    await db.close()
    extra = f" broker_reportou_conectados={reportado}" if conexoes > 1 else ""
    print(f"RESULTADO lote={lote} conexoes={len(clientes)}{extra} enviadas={enviadas} gravadas={gravadas} "
          f"perdidas={enviadas - gravadas}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("totem")
    a.add_argument("--intervalo", type=float, default=3.0)
    b = sub.add_parser("carga")
    b.add_argument("--taxa", type=int, default=50)
    b.add_argument("--total", type=int, default=3000)
    b.add_argument("--sessoes", type=int, default=1000)
    b.add_argument("--conexoes", type=int, default=1, help="conexões MQTT reais simultâneas (RNF06: 1000)")
    args = ap.parse_args()
    if args.cmd == "totem":
        asyncio.run(totem(args.intervalo))
    else:
        asyncio.run(carga(args.taxa, args.total, args.sessoes, args.conexoes))
