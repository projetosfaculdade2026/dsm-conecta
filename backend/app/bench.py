"""Carga sintética de 1M de registros + comparação de desempenho (Iteração 3).

  python -m app.bench --n 1000000
"""
import argparse
import asyncio
import statistics
import time

import asyncpg

from .config import settings

COLS = "event_id, ts, session_id, categoria, origem, schema_version, payload"


async def medir(c, sql, vezes=5):
    tempos = []
    for _ in range(vezes):
        t = time.perf_counter()
        await c.fetch(sql)
        tempos.append((time.perf_counter() - t) * 1000)
    return statistics.median(tempos)


async def main(n: int):
    c = await asyncpg.connect(settings.database_url)
    print(f"Inserindo {n} registros sintéticos...")
    t = time.perf_counter()
    await c.execute(f"""
        INSERT INTO telemetria({COLS})
        SELECT gen_random_uuid(), now() - random() * interval '30 days', md5(random()::text),
               (ARRAY['interacao','quiz','sensor'])[1 + floor(random()*3)::int], 'app', 1,
               jsonb_build_object('tela', (ARRAY['inicio','curso','eventos','quiz','painel'])[1 + floor(random()*5)::int],
                                  'questao', 1, 'perfil', 'web', 'lote', 'bench')
        FROM generate_series(1, {n}) ON CONFLICT DO NOTHING""")
    print(f"  inserção: {time.perf_counter() - t:.1f}s")
    await c.execute("DROP TABLE IF EXISTS telemetria_plana")
    await c.execute(f"CREATE TABLE telemetria_plana AS SELECT {COLS} FROM telemetria")  # sem partição e sem índice
    await c.execute("CALL refresh_continuous_aggregate('telemetria_hora', NULL, NULL)")
    await c.execute("ANALYZE telemetria; ANALYZE telemetria_plana;")
    total = await c.fetchval("SELECT count(*) FROM telemetria")
    print(f"Total na hypertable: {total}\n")

    consultas = {
        "Últimas 24h por categoria": (
            "SELECT categoria, count(*) FROM {t} WHERE ts > now() - interval '24 hours' GROUP BY 1"),
        "Última hora por categoria": (
            "SELECT categoria, count(*) FROM {t} WHERE ts > now() - interval '1 hour' GROUP BY 1"),
    }
    print(f"{'Consulta':40s} {'plana (ms)':>12s} {'hypertable (ms)':>16s}")
    for nome, sql in consultas.items():
        a = await medir(c, sql.format(t="telemetria_plana"))
        b = await medir(c, sql.format(t="telemetria"))
        print(f"{nome:40s} {a:12.1f} {b:16.1f}")
    bruto = await medir(c, "SELECT categoria, count(*) FROM telemetria WHERE ts > now() - interval '30 days' GROUP BY 1")
    agreg = await medir(c, "SELECT categoria, sum(total) FROM telemetria_hora GROUP BY 1")
    print(f"\nTotal 30 dias: bruto={bruto:.1f} ms | agregação contínua={agreg:.1f} ms")
    await c.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1_000_000)
    asyncio.run(main(ap.parse_args().n))
