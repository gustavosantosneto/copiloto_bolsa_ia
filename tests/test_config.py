import pytest

from copiloto.config import TOML_PADRAO, ErroConfig, carregar_config, ler_credenciais

TOML_BASE = TOML_PADRAO.read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def _sem_env_mt5(monkeypatch):
    import os
    for k in list(os.environ):
        if k.startswith("MT5_"):
            monkeypatch.delenv(k)


def _carrega(tmp_path, troca: tuple[str, str] | None = None, env: str = ""):
    texto = TOML_BASE
    if troca:
        assert troca[0] in texto, f"trecho não achado: {troca[0]}"
        texto = texto.replace(troca[0], troca[1])
    (tmp_path / "p.toml").write_text(texto, encoding="utf-8")
    (tmp_path / ".env").write_text(env, encoding="utf-8")
    return carregar_config(tmp_path / "p.toml", tmp_path / ".env")


def test_config_real_carrega(tmp_path):
    cfg = _carrega(tmp_path)
    assert cfg.geral.ambiente == "demo"
    assert cfg.operacao.lote_padrao % 100 == 0
    assert len(cfg.universo.watchlist) == 17


@pytest.mark.parametrize("troca, campo", [
    (("lote_padrao = 100", "lote_padrao = 150"), "operacao.lote_padrao"),
    (('ambiente = "demo"', 'ambiente = "xyz"'), "geral.ambiente"),
    (("perda_max_dia = 20", "perda_max_dia = 120"), "risco.perda_max_dia"),
    (('janela_operacao_fim = "15:00"', 'janela_operacao_fim = "18:00"'), "pregao"),
    (('principal = "M12"', 'principal = "M7"'), "timeframes"),
    (("moeda = \"BRL\"", "moeda = \"BRL\"\nmoeda_x = 1"), "geral.moeda_x"),
])
def test_valor_invalido_aponta_campo(tmp_path, troca, campo):
    with pytest.raises(ErroConfig, match=campo.replace(".", r"\.")):
        _carrega(tmp_path, troca)


def test_toml_quebrado(tmp_path):
    with pytest.raises(ErroConfig, match="TOML inválido"):
        _carrega(tmp_path, ("perda_max_dia = 20", "perda_max_dia = 50%"))


def test_watchlist_normalizada(tmp_path):
    cfg = _carrega(tmp_path, ('"ABEV3",', '" abev3 ",'))
    assert cfg.universo.watchlist[0] == "ABEV3"


def test_credenciais_ausentes_nao_quebram(tmp_path):
    cfg = _carrega(tmp_path)
    assert not cfg.credenciais.completas


def test_credenciais_do_ambiente_escolhido(tmp_path):
    env = "MT5_DEMO_LOGIN=123\nMT5_DEMO_SENHA=s3nh4\nMT5_DEMO_SERVIDOR=XP-DEMO\nMT5_REAL_LOGIN=999\n"
    cfg = _carrega(tmp_path, env=env)
    assert cfg.credenciais.completas
    assert cfg.credenciais.login == 123
    assert "s3nh4" not in cfg.model_dump_json()  # senha mascarada


def test_login_nao_numerico():
    with pytest.raises(ErroConfig, match="login"):
        ler_credenciais("demo", {"MT5_DEMO_LOGIN": "abc"})
