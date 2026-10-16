"""Motor de análise em tempo real: janela deslizante, média móvel, desvio estatístico."""
import statistics
import time
from collections import Counter, defaultdict, deque


JANELA_MIN, JANELA_MAX = 10, 3600  # RF20: limites da janela deslizante configurável (segundos)


class SlidingWindow:
    def __init__(self, seconds: float):
        self.seconds = seconds  # retenção máxima dos itens
        self._d: deque = deque()

    def add(self, item, t: float | None = None) -> None:
        self._d.append((time.time() if t is None else t, item))

    def items(self, now: float | None = None, seconds: float | None = None) -> list:
        """Itens da janela. `seconds` (<= retenção) estreita a janela sem descartar o histórico retido."""
        now = time.time() if now is None else now
        while self._d and self._d[0][0] <= now - self.seconds:
            self._d.popleft()
        if seconds is None or seconds >= self.seconds:
            return [i for _, i in self._d]
        corte = now - seconds
        return [i for t, i in self._d if t > corte]


def moving_average(values: list[float], n: int) -> list[float]:
    if n <= 0:
        raise ValueError("n deve ser positivo")
    out = []
    for i in range(len(values)):
        w = values[max(0, i - n + 1): i + 1]
        out.append(sum(w) / len(w))
    return out


def zscore(history: list[float], current: float) -> float:
    mean = statistics.fmean(history)
    std = max(statistics.pstdev(history), 1.0)  # piso evita divisão por ~0
    return (current - mean) / std


def is_anomaly(history: list[float], current: float, threshold: float = 3.0, min_samples: int = 5) -> bool:
    if len(history) < min_samples:
        return False
    return zscore(history, current) > threshold


class Engine:
    def __init__(self, window: int = 60, bucket: int = 5, hist: int = 12, threshold: float = 3.0):
        self.janela = window  # janela de análise em segundos (configurável, RF20)
        self.win = SlidingWindow(max(window, JANELA_MAX))  # retém o máximo permitido; a janela só filtra
        self.bucket, self.hist, self.threshold = bucket, hist, threshold
        self.buckets: dict[int, int] = defaultdict(int)
        self.presencas: dict[str, set] = defaultdict(set)  # RN05: 1 presença/sessão/evento
        self.quiz: Counter = Counter()
        self.total = 0

    def ingest(self, ev, now: float | None = None) -> None:
        now = time.time() if now is None else now
        self.total += 1
        self.win.add((ev.session_id, ev.categoria, ev.payload.get("tela"), ev.origem), now)
        self.buckets[int(now // self.bucket)] += 1
        if ev.categoria == "presenca":
            self.presencas[str(ev.payload["evento_id"])].add(ev.session_id)
        if ev.categoria == "quiz":
            self.quiz[ev.payload["perfil"]] += 1

    def set_janela(self, segundos: int) -> None:
        """RF20: altera a janela do ranking e dos visitantes ativos (10 s a 1 h)."""
        if isinstance(segundos, bool) or not isinstance(segundos, int) or not JANELA_MIN <= segundos <= JANELA_MAX:
            raise ValueError(f"janela deve ser inteiro entre {JANELA_MIN} e {JANELA_MAX} segundos")
        self.janela = segundos

    def visitantes_ativos(self, now=None) -> int:
        return len({s for s, _, _, o in self.win.items(now, self.janela) if o == "app"})

    def ranking(self, now=None, top: int = 5) -> list[dict]:
        c = Counter(t for _, cat, t, _ in self.win.items(now, self.janela) if cat == "interacao" and t)
        return [{"tela": t, "total": n} for t, n in c.most_common(top)]

    def serie(self, now=None) -> list[int]:
        cur = int((time.time() if now is None else now) // self.bucket)
        return [self.buckets.get(cur - self.hist + 1 + i, 0) for i in range(self.hist)]

    def alerta(self, now=None) -> dict:
        """Compara o último bucket concluído com o histórico anterior (z-score)."""
        now = time.time() if now is None else now
        cur = int(now // self.bucket)
        hist = [self.buckets.get(cur - i, 0) for i in range(2, 2 + self.hist)]
        atual = self.buckets.get(cur - 1, 0)
        for k in [k for k in self.buckets if k < cur - self.hist - 3]:
            del self.buckets[k]
        return {"anomalia": is_anomaly(hist, atual, self.threshold), "atual": atual,
                "media": round(statistics.fmean(hist), 2)}

    def snapshot(self, now=None) -> dict:
        now = time.time() if now is None else now
        s = self.serie(now)
        return {
            "ts": now, "total": self.total, "janela_s": self.janela,
            "visitantes_ativos": self.visitantes_ativos(now),
            "ranking": self.ranking(now),
            "presencas": {k: len(v) for k, v in self.presencas.items()},
            "quiz": dict(self.quiz), "serie": s,
            "media_movel": [round(x, 2) for x in moving_average(s, 3)],
            "alerta": self.alerta(now),
        }
