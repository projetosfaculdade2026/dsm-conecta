import asyncio
import json

import asyncpg

from .config import settings

INSERT_SQL = (
    "INSERT INTO telemetria(event_id, ts, session_id, categoria, origem, schema_version, payload) "
    "VALUES($1,$2,$3,$4,$5,$6,$7::jsonb) ON CONFLICT DO NOTHING"
)


async def create_pool() -> asyncpg.Pool:
    for tentativa in range(10):
        try:
            return await asyncpg.create_pool(settings.database_url, min_size=1, max_size=10)
        except (OSError, asyncpg.PostgresError):
            await asyncio.sleep(min(2 ** tentativa, 5))
    raise RuntimeError("banco indisponível")


async def inserir_lote(pool, eventos) -> None:
    rows = [(e.event_id, e.ts, e.session_id, e.categoria, e.origem, e.schema_version,
             json.dumps(e.payload)) for e in eventos]
    async with pool.acquire() as c:
        await c.executemany(INSERT_SQL, rows)  # ON CONFLICT: deduplicação entre instâncias (RNF07)
