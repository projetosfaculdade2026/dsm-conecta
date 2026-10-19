from app.quiz import perfil_predominante


def test_perfil_mais_escolhido_vence():
    assert perfil_predominante(["web", "dados", "dados", "infra"]) == "dados"


def test_empate_fica_com_o_que_apareceu_primeiro():
    assert perfil_predominante(["mobile", "web", "web", "mobile"]) == "mobile"


def test_sem_respostas_nao_ha_perfil():
    assert perfil_predominante([]) is None


def test_ignora_perfil_desconhecido():
    assert perfil_predominante(["xyz", "web"]) == "web"
