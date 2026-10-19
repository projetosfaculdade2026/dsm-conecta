from collections import Counter

PERFIS = ("web", "mobile", "dados", "infra")


def perfil_predominante(respostas: list[str]) -> str | None:
    """Devolve o perfil mais escolhido. Se houver empate, vale o que apareceu primeiro."""
    validas = [r for r in respostas if r in PERFIS]
    if not validas:
        return None
    contagem = Counter(validas)
    maior = max(contagem.values())
    return next(r for r in validas if contagem[r] == maior)
