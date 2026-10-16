import asyncio
import json

from conftest import evento

from app.dedup import Dedup
from app.ingest import processar


def _rodar(topic, raw, fila=None, dedup=None):
    fila = fila or asyncio.Queue()
    dedup = dedup or Dedup()
    stats = {"invalidas": 0, "duplicadas": 0}
    asyncio.run(processar(topic, raw, fila, dedup, stats))
    return fila, stats


def test_valida_entra_na_fila():
    fila, stats = _rodar("dsm/prod/app/interacao/tela", json.dumps(evento()))
    assert fila.qsize() == 1 and stats["invalidas"] == 0


def test_malformada_descartada():
    fila, stats = _rodar("dsm/prod/app/interacao/tela", b"lixo")
    assert fila.qsize() == 0 and stats["invalidas"] == 1


def test_topico_incompativel():
    fila, stats = _rodar("dsm/prod/totem/interacao/tela", json.dumps(evento()))
    assert fila.qsize() == 0 and stats["invalidas"] == 1


def test_duplicada_descartada():
    raw = json.dumps(evento())
    dedup, fila = Dedup(), asyncio.Queue()
    stats = {"invalidas": 0, "duplicadas": 0}

    async def dois():
        await processar("dsm/prod/app/interacao/tela", raw, fila, dedup, stats)
        await processar("dsm/prod/app/interacao/tela", raw, fila, dedup, stats)

    asyncio.run(dois())
    assert fila.qsize() == 1 and stats["duplicadas"] == 1


def test_status_ignorado():
    fila, stats = _rodar("dsm/prod/totem/status/sensor-01", b"offline")
    assert fila.qsize() == 0 and stats["invalidas"] == 0
