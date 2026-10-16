from datetime import datetime, timezone

from app.opendata import CAMPOS, DICIONARIO, para_csv, preparar_publicacao, relatorio_escola


def test_dicionario_descreve_exatamente_as_colunas_publicadas():  # RNF03
    assert [c["nome"] for c in DICIONARIO["campos"]] == CAMPOS


def test_preparar_aplica_rn08_e_remove_presenca():
    linhas = [
        {"hora": "h1", "categoria": "interacao", "total": 10},
        {"hora": "h1", "categoria": "quiz", "total": 9},
        {"hora": "h1", "categoria": "presenca", "total": 500},
    ]
    assert preparar_publicacao(linhas) == [{"hora": "h1", "categoria": "interacao", "total": 10}]


def test_preparar_descarta_colunas_extras():
    linhas = [{"hora": "h", "categoria": "sensor", "total": 11, "session_id": "segredo"}]
    assert "session_id" not in preparar_publicacao(linhas)[0]


def test_csv_tem_cabecalho_mesmo_sem_dados():
    assert para_csv([]) == "hora,categoria,total\n"


def test_csv_com_dados():
    assert para_csv([{"hora": "h", "categoria": "quiz", "total": 12}]) == "hora,categoria,total\nh,quiz,12\n"


def test_relatorio_mascara_grupos_pequenos():
    txt = relatorio_escola([("inicio", 12), ("curso", 9)], [("web", 3)], [("Feira", 10)],
                           agora=datetime(2026, 10, 1, 12, tzinfo=timezone.utc))
    assert "| inicio | 12 |" in txt and "| curso |" not in txt
    assert "| Feira | 10 |" in txt
    assert "Sem dados suficientes" in txt  # perfis com 3 registros não aparecem
    assert "01/10/2026 12:00" in txt


def test_relatorio_vazio_nao_quebra():
    txt = relatorio_escola([], [], [])
    assert txt.count("Sem dados suficientes") == 3
