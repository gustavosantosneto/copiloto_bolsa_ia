"""Capacidade: cada limite em lotes, menor vence; simulação só na demo."""

import pytest

from copiloto.capacidade import calcular
from copiloto.config import carregar_config


def _cfg(**risco):
    cfg = carregar_config()
    cfg.simulacao.capital_simulado, cfg.simulacao.alavancagem_simulada = 5000.0, 200.0
    for k, v in risco.items():
        setattr(cfg.risco, k, v)
    return cfg


SIMB = [{"ticker": "RADL3", "existe": True, "ask": 20.0, "ultimo": 20.0},
        {"ticker": "XXXX3", "existe": False}]
CONTA_DEMO = {"patrimonio": 1_000_000.0, "margem": 0.0, "margem_livre": 1_000_000.0}
SEM_MT5 = lambda t, v, p: None  # noqa: E731 — simulado não deve chamar


def _radl(r):
    return r["ativos"][0]


def test_simulado_usa_capital_e_alavancagem():
    r = calcular(_cfg(exposicao_max_ativo_pct=1000, exposicao_max_total_pct=1000, margem_usada_max_pct=100),
                 CONTA_DEMO, [], SIMB, SEM_MT5)
    a = _radl(r)
    assert r["modo"] == "simulado" and r["conta"]["patrimonio"] == 5000.0
    assert (a["valor_lote"], a["margem_lote"]) == (2000.0, 10.0)
    assert a["lotes_por_limite"]["margem_livre"] == 500
    assert a["lotes_por_limite"]["exposicao_ativo"] == 25  # 10x 5000 / 2000
    assert (a["lotes_operaveis"], a["restricao"]) == (25, "exposicao_ativo")


def test_posicao_atual_consome_limites():
    pos = [{"ticker": "RADL3", "volume": 1000.0, "preco_atual": 20.0, "lucro": -100.0}]
    r = calcular(_cfg(exposicao_max_ativo_pct=1000, exposicao_max_total_pct=1000, margem_usada_max_pct=100),
                 CONTA_DEMO, pos, SIMB, SEM_MT5)
    a = _radl(r)
    assert r["conta"] == {"patrimonio": 4900.0, "margem_usada": 100.0, "margem_livre": 4800.0, "valor_posicoes": 20000.0}
    assert a["qtd_carteira"] == 1000.0
    assert a["lotes_por_limite"]["exposicao_ativo"] == 14  # (49000 - 20000) / 2000


def test_sem_cotacao_zera():
    r = calcular(_cfg(), CONTA_DEMO, [], SIMB, SEM_MT5)
    assert r["ativos"][1] == {"ticker": "XXXX3", "preco": None, "qtd_carteira": 0, "lotes_operaveis": 0,
                              "restricao": "sem_cotacao"}


def test_fora_universo_ignorada_no_simulado():
    pos = [{"ticker": "WDOG26", "volume": 1.0, "preco_atual": 5230.0, "lucro": 50.0}]
    r = calcular(_cfg(), CONTA_DEMO, pos, SIMB, SEM_MT5)
    assert r["ignoradas_fora_universo"] == ["WDOG26"] and r["conta"]["patrimonio"] == 5000.0


@pytest.mark.parametrize("capital", [0.0, 5000.0])
def test_real_ou_sem_capital_usa_conta_e_mt5(capital):
    cfg = _cfg(exposicao_max_ativo_pct=1000, exposicao_max_total_pct=1000, margem_usada_max_pct=100)
    cfg.simulacao.capital_simulado = capital
    if capital:
        cfg.geral.ambiente = "real"
    conta = {"patrimonio": 5000.0, "margem": 0.0, "margem_livre": 5000.0}
    r = calcular(cfg, conta, [], SIMB, lambda t, v, p: 20.0)
    assert r["modo"] == "conta" and _radl(r)["margem_lote"] == 20.0
