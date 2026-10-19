"""ServicoMT5 com SDK falso — não precisa do terminal aberto."""

from types import SimpleNamespace as NS

import pytest

from copiloto import mt5_servico
from copiloto.config import TOML_PADRAO, carregar_config
from copiloto.mt5_servico import ErroMT5, ServicoMT5

ENV_OK = "MT5_DEMO_LOGIN=1\nMT5_DEMO_SENHA=x\nMT5_DEMO_SERVIDOR=S\nMT5_REAL_LOGIN=2\nMT5_REAL_SENHA=y\nMT5_REAL_SERVIDOR=R\n"


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    import os
    for k in list(os.environ):
        if k.startswith("MT5_"):
            monkeypatch.delenv(k)

    def _cfg(ambiente="demo", env=ENV_OK):
        texto = TOML_PADRAO.read_text(encoding="utf-8").replace('ambiente = "demo"', f'ambiente = "{ambiente}"')
        texto = texto.replace("intervalo_reconexao_s = 5", "intervalo_reconexao_s = 0.01")
        (tmp_path / "p.toml").write_text(texto, encoding="utf-8")
        (tmp_path / ".env").write_text(env, encoding="utf-8")
        return carregar_config(tmp_path / "p.toml", tmp_path / ".env")
    return _cfg


@pytest.fixture
def sdk(monkeypatch):
    f = NS(
        init_ok=[True], chamadas_init=0, trade_mode=0,
        shutdown=lambda: None, last_error=lambda: (-1, "falha"),
        symbol_info=lambda t: NS(visible=True, volume_min=100, volume_step=100, trade_contract_size=1,
                                 margin_initial=0.0, trade_calc_mode=32) if t == "ABEV3" else None,
        symbol_info_tick=lambda t: NS(bid=1.0, ask=1.1, last=1.05, time_msc=1_760_000_000_000),
    )

    def initialize(**kw):
        f.chamadas_init += 1
        return f.init_ok.pop(0) if f.init_ok else False
    f.initialize = initialize
    f.account_info = lambda: NS(trade_mode=f.trade_mode)
    monkeypatch.setattr(mt5_servico, "mt5", f)
    return f


def test_sem_credenciais_nem_tenta(cfg, sdk):
    with pytest.raises(ErroMT5, match="incompletas"):
        ServicoMT5(cfg(env="")).conectar()
    assert sdk.chamadas_init == 0


def test_reconecta_ate_limite(cfg, sdk):
    sdk.init_ok = [False, False, True]
    ServicoMT5(cfg()).conectar()
    assert sdk.chamadas_init == 3


def test_falha_apos_tentativas(cfg, sdk):
    sdk.init_ok = []
    c = cfg()
    with pytest.raises(ErroMT5, match="initialize"):
        ServicoMT5(c).conectar()
    assert sdk.chamadas_init == c.mt5.tentativas_reconexao + 1


@pytest.mark.parametrize("ambiente, trade_mode", [("demo", 2), ("real", 0)])
def test_conta_diferente_do_ambiente_bloqueia(cfg, sdk, ambiente, trade_mode):
    sdk.trade_mode = trade_mode
    with pytest.raises(ErroMT5, match="config pede"):
        ServicoMT5(cfg(ambiente)).conectar()


def test_simbolo_inexistente_nao_quebra(cfg, sdk):
    r = ServicoMT5(cfg()).simbolos(["ABEV3", "WDOG26"])
    assert r[0]["existe"] and r[0]["bid"] == 1.0
    assert r[1] == {"ticker": "WDOG26", "existe": False}
