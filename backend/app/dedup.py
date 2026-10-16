from collections import OrderedDict


class Dedup:
    """Cache LRU de identificadores vistos (deduplicação em memória)."""

    def __init__(self, capacidade: int = 200_000):
        self._d: OrderedDict[str, None] = OrderedDict()
        self.cap = capacidade

    def visto(self, chave: str) -> bool:
        if chave in self._d:
            self._d.move_to_end(chave)
            return True
        self._d[chave] = None
        if len(self._d) > self.cap:
            self._d.popitem(last=False)
        return False
