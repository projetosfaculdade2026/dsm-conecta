import uuid
from datetime import datetime, timezone


def evento(**kw):
    base = {"event_id": str(uuid.uuid4()), "session_id": "sessao-abc12345", "categoria": "interacao",
            "origem": "app", "ts": datetime.now(timezone.utc).isoformat(), "schema_version": 1,
            "payload": {"tela": "inicio"}}
    base.update(kw)
    return base
