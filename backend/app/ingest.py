"""Serviço de ingestão assíncrono: assina o broker, valida, deduplica e grava em lote."""
import asyncio
import json
import socket
import time

import aiomqtt

from .config import settings
from .db import create_pool, inserir_lote
from .dedup import Dedup
from .schema import parse_message, topic_ok


def log(evento: str, **kw) -> None:  # log estruturado (RF17)
    print(json.dumps({"ts": time.time(), "evento": evento, **kw}, default=str), flush=True)


async def processar(topic: str, raw, fila: asyncio.Queue, dedup: Dedup, stats: dict) -> None:
    partes = topic.split("/")
    if len(partes) > 3 and partes[3] == "status":  # mensagens de presença (LWT), não são telemetria
        return
    try:
        ev = parse_message(raw)
        if not topic_ok(topic, ev):
            raise ValueError("tópico incompatível com a mensagem")
    except (ValueError, TypeError) as e:
        stats["invalidas"] += 1
        log("mensagem_descartada", motivo="malformada", topico=topic, erro=str(e)[:200])
        return
    if dedup.visto(str(ev.event_id)):
        stats["duplicadas"] += 1
        log("mensagem_descartada", motivo="duplicada", event_id=str(ev.event_id))
        return
    await fila.put(ev)  # fila limitada => contrapressão (RNF09)


async def consumidor(fila, dedup, stats) -> None:
    while True:
        try:
            async with aiomqtt.Client(hostname=settings.mqtt_host, port=settings.mqtt_port,
                                      username=settings.mqtt_user, password=settings.mqtt_pass,
                                      identifier=f"dsm-ingest-{socket.gethostname()}") as c:
                await c.subscribe("$share/ingestao/dsm/+/+/+/+", qos=1)  # assinatura compartilhada: réplicas dividem a carga
                log("mqtt_conectado")
                async for m in c.messages:
                    await processar(str(m.topic), m.payload, fila, dedup, stats)
        except aiomqtt.MqttError as e:
            log("mqtt_erro", erro=str(e))
            await asyncio.sleep(2)


async def escritor(pool, fila, stats, lote: int = 500, espera: float = 0.5) -> None:
    while True:
        batch = [await fila.get()]
        fim = time.monotonic() + espera
        while len(batch) < lote:
            resta = fim - time.monotonic()
            if resta <= 0:
                break
            try:
                batch.append(await asyncio.wait_for(fila.get(), resta))
            except asyncio.TimeoutError:
                break
        for tentativa in range(5):
            try:
                await inserir_lote(pool, batch)
                stats["gravadas"] += len(batch)
                break
            except Exception as e:  # noqa: BLE001
                log("erro_gravacao", erro=str(e)[:200], tentativa=tentativa)
                await asyncio.sleep(min(2 ** tentativa, 10))
        else:
            stats["perdidas"] += len(batch)


async def relatorio(stats) -> None:
    while True:
        await asyncio.sleep(10)
        log("stats", **stats)


async def main() -> None:
    pool = await create_pool()
    fila: asyncio.Queue = asyncio.Queue(maxsize=5000)
    stats = {"gravadas": 0, "invalidas": 0, "duplicadas": 0, "perdidas": 0}
    await asyncio.gather(consumidor(fila, Dedup(), stats), escritor(pool, fila, stats), relatorio(stats))


if __name__ == "__main__":
    asyncio.run(main())
