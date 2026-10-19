"""Regras de negócio puras (RN03, RN04, RN05, RN08)."""
from datetime import datetime
from math import asin, cos, radians, sin, sqrt

MIN_GRUPO = 10  # RN08
RAIO_METROS = 150  # RN04


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6371000
    p1, p2 = radians(lat1), radians(lat2)
    dp, dl = p2 - p1, radians(lon2 - lon1)
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * r * asin(sqrt(a))


def dentro_do_raio(lat, lon, lat0, lon0, raio=RAIO_METROS) -> bool:
    return haversine_m(lat, lon, lat0, lon0) <= raio


def _norm(codigo: str) -> str:
    """Código do evento sem espaços nas pontas e sem diferença entre maiúsculas e minúsculas (RF10)."""
    return codigo.strip().casefold()


def _coord(v, minimo: float, maximo: float) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if minimo <= f <= maximo else None


def presenca_valida(extra: dict, agora: datetime, codigo: str | None,
                    lat: float | None = None, lon: float | None = None) -> tuple[bool, str]:
    """RN03 (janela de horário), RF10 (código do QR) e RF11/RN04 (proximidade de até 150 m).

    A presença vale por **código** (quando informado) ou por **localização** (quando o código não é informado).
    """
    ini = datetime.fromisoformat(extra["inicio"])
    fim = datetime.fromisoformat(extra["fim"])
    if not ini <= agora <= fim:
        return False, "fora da janela de horário do evento"
    esperado = extra.get("codigo")
    local = extra.get("lat"), extra.get("lon")
    tem_local = None not in local

    if codigo:  # presença por código / QR
        if esperado and _norm(codigo) != _norm(esperado):
            return False, "código do evento inválido"
        return True, "ok"

    if lat is not None or lon is not None:  # presença por geolocalização (RN04)
        la, lo = _coord(lat, -90, 90), _coord(lon, -180, 180)
        if la is None or lo is None:
            return False, "localização inválida"
        if not tem_local:
            return False, "este evento não aceita presença por localização"
        if not dentro_do_raio(la, lo, float(local[0]), float(local[1])):
            return False, f"fora do raio de {RAIO_METROS} m do local do evento"
        return True, "ok"

    if esperado:
        return False, "código do evento inválido"
    if tem_local:
        return False, "informe o código do evento ou autorize a localização"
    return True, "ok"


def mascarar_grupo(linhas: list[dict], campo: str = "total", minimo: int = MIN_GRUPO) -> list[dict]:
    """RN08: só divulga grupos com no mínimo `minimo` registros."""
    return [x for x in linhas if x[campo] >= minimo]
