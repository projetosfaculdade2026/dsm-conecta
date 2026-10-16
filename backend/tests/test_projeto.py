"""Verificações de coerência do repositório (documentos, ACL e banco) para que não se afastem do código."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def _ler(rel: str) -> str:
    return (RAIZ / rel).read_text(encoding="utf-8")


def test_termo_do_app_e_do_repositorio_sao_o_mesmo_texto():  # seção 11 do Documento de Visão
    dart = _ler("app/lib/consent_text.dart")
    trecho = dart.split("// BEGIN-TERMO", 1)[1].split("// END-TERMO", 1)[0]
    paragrafos = re.findall(r"^\s*'(.+)',\s*$", trecho, flags=re.M)
    assert len(paragrafos) >= 8
    termo = _ler("docs/TERMO_DE_CONSENTIMENTO.md")
    for p in paragrafos:
        assert p in termo, f"parágrafo do app ausente no termo: {p[:50]}"


def test_termo_cita_lgpd_revogacao_e_exclusao():
    termo = _ler("docs/TERMO_DE_CONSENTIMENTO.md")
    for chave in ("13.709", "revogar", "excluir", "código aleatório", "90 dias"):
        assert chave in termo


def test_dicionario_de_dados_documenta_todos_os_campos():
    from app.opendata import DICIONARIO
    doc = _ler("docs/DICIONARIO_DE_DADOS.md")
    for c in DICIONARIO["campos"]:
        assert f"`{c['nome']}`" in doc


def test_acl_restringe_totem_e_leitor():  # Iteração 2: autenticação e controle de acesso no broker
    acl = _ler("mosquitto/acl")
    assert "user totem" in acl and "user leitor" in acl
    assert "topic write dsm/+/totem/sensor/+" in acl
    assert "topic read dsm/#" in acl
    totem = acl.split("user totem", 1)[1].split("user leitor", 1)[0]
    assert "/app/" not in totem  # o totem não pode escrever em tópicos do app


def test_broker_usa_acl_e_senha():
    conf = _ler("mosquitto/mosquitto.conf")
    assert "allow_anonymous false" in conf and "acl_file" in conf and "password_file" in conf


def test_so_scripts_sql_numerados_no_banco():
    """Um init.sql legado rodando depois de 01_schema.sql derruba a criação do banco."""
    nomes = sorted(p.name for p in (RAIZ / "db").glob("*.sql"))
    assert nomes == ["01_schema.sql", "02_policies.sql", "03_seed.sql"]


def test_tabela_presencas_tem_chave_unica_por_sessao_e_evento():  # RN05
    sql = _ler("db/01_schema.sql")
    assert re.search(r"CREATE TABLE presencas.*PRIMARY KEY \(evento_id, session_id\)", sql, flags=re.S)


def test_nenhum_segredo_versionado():
    assert ".env" in _ler(".gitignore").splitlines()
