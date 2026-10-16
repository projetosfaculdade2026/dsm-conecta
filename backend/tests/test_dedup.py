from app.dedup import Dedup


def test_duplicada():
    d = Dedup()
    assert d.visto("a") is False
    assert d.visto("a") is True


def test_lru_descarta_antigos():
    d = Dedup(capacidade=2)
    d.visto("a"); d.visto("b"); d.visto("c")
    assert d.visto("a") is False  # 'a' foi descartado
