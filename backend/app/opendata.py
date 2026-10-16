"""Dados abertos (RNF03, RN08) e relatório agregado para a escola parceira (seção 9 do Documento de Visão).

Funções puras: recebem linhas já consultadas e devolvem texto. Nada aqui acessa banco ou rede.
"""
import csv
import io
from datetime import datetime, timezone

from .rules import MIN_GRUPO, mascarar_grupo

CAMPOS = ["hora", "categoria", "total"]

# Dicionário de dados: a mesma estrutura é servida em /open-data/dicionario e descrita em docs/DICIONARIO_DE_DADOS.md.
DICIONARIO = {
    "conjunto": "telemetria_agregada_por_hora",
    "descricao": "Contagem de eventos de uso do aplicativo DSM Conecta por hora e categoria, em nível agregado.",
    "licenca": "CC BY 4.0",
    "formatos": ["csv", "json"],
    "regras_de_publicacao": [
        f"Somente grupos (hora + categoria) com no mínimo {MIN_GRUPO} registros são divulgados (RN08).",
        "Não há identificador de sessão, dispositivo, localização nem qualquer dado pessoal (RNF15, RNF16).",
        "A categoria 'presenca' não é publicada neste conjunto.",
    ],
    "campos": [
        {"nome": "hora", "tipo": "texto (ISO-8601, UTC)", "descricao": "Início da hora a que a contagem se refere.",
         "exemplo": "2026-10-01T14:00:00+00:00"},
        {"nome": "categoria", "tipo": "texto", "descricao": "Tipo de evento: interacao, quiz ou sensor.",
         "exemplo": "interacao"},
        {"nome": "total", "tipo": "inteiro >= 10", "descricao": "Quantidade de eventos da categoria na hora.",
         "exemplo": "42"},
    ],
}

CATEGORIAS_PUBLICAS = {"interacao", "quiz", "sensor"}


def preparar_publicacao(linhas: list[dict]) -> list[dict]:
    """Aplica RN08 e remove categorias não publicáveis. Cada linha: {hora, categoria, total}."""
    visiveis = [x for x in linhas if x["categoria"] in CATEGORIAS_PUBLICAS]
    return [{c: x[c] for c in CAMPOS} for x in mascarar_grupo(visiveis)]


def para_csv(linhas: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CAMPOS, lineterminator="\n")
    w.writeheader()
    w.writerows(linhas)
    return buf.getvalue()


def _tabela(titulo: str, cab: tuple[str, str], linhas: list[tuple[str, int]]) -> list[str]:
    out = [f"### {titulo}", ""]
    visiveis = [(k, n) for k, n in linhas if n >= MIN_GRUPO]
    if not visiveis:
        return out + [f"_Sem dados suficientes (mínimo de {MIN_GRUPO} registros por grupo)._", ""]
    out += [f"| {cab[0]} | {cab[1]} |", "|---|---:|"]
    out += [f"| {k} | {n} |" for k, n in visiveis]
    return out + [""]


def relatorio_escola(telas: list[tuple[str, int]], perfis: list[tuple[str, int]],
                     presencas: list[tuple[str, int]], agora: datetime | None = None) -> str:
    """Devolutiva agregada para a escola parceira. Grupos com menos de 10 registros não aparecem (RN08)."""
    agora = agora or datetime.now(timezone.utc)
    linhas = [
        "# Devolutiva da ação de divulgação — DSM Conecta", "",
        f"Gerado em {agora.strftime('%d/%m/%Y %H:%M')} (UTC). Curso Superior de Tecnologia em "
        "Desenvolvimento de Software Multiplataforma, Fatec Zona Sul.", "",
        "Este relatório reúne apenas dados agregados e anonimizados. Não há nome, contato nem "
        f"identificação individual, e grupos com menos de {MIN_GRUPO} registros não são divulgados.", "",
        "## O que os estudantes mais exploraram", "",
    ]
    linhas += _tabela("Telas mais acessadas", ("Tela", "Acessos"), telas)
    linhas += _tabela("Perfis de afinidade (questionário vocacional)", ("Perfil", "Respostas"), perfis)
    linhas += _tabela("Presenças registradas por evento", ("Evento", "Presenças"), presencas)
    linhas += [
        "## Sobre o questionário", "",
        "O resultado do questionário é apenas orientativo e não tem qualquer efeito sobre processo seletivo (RN06).", "",
        "## Contato", "",
        "Coordenação do curso DSM — Fatec Zona Sul. Dúvidas e novas ações: use o canal "
        "\"Falar com a coordenação\" no aplicativo.", "",
    ]
    return "\n".join(linhas)
