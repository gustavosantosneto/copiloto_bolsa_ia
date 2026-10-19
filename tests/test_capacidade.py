"""Capacidade: cada limite em lotes, menor vence; simulação só na demo."""

from datetime import datetime

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
CONTA_DEMO = {"saldo": 1_000_000.0, "patrimonio": 1_000_000.0, "margem": 0.0, "margem_livre": 1_000_000.0}
FORA = datetime(2026, 10, 19, 20, 0)  # fora do pregão: cotação sem tick novo é aceita
SEM_MT5 = lambda t, v, p: None  # noqa: E731 — simulado não deve chamar


def _radl(r):
    return r["ativos"][0]


def test_simulado_usa_capital_e_alavancagem():
    r = calcular(_cfg(margem_usada_max_pct=100), CONTA_DEMO, [], SIMB, SEM_MT5, FORA)
    a = _radl(r)
    assert r["modo"] == "simulado" and r["conta"]["saldo"] == 5000.0
    assert (a["valor_lote"], a["margem_lote"]) == (2000.0, 10.0)
    assert a["lotes_por_limite"]["margem_livre"] == 500
    assert (a["lotes_operaveis"], a["restricao"]) == (15, "max_lotes_ativo")
    assert a["folga_perda_ativo"] == 500.0  # 10% de 5000, posição zerada


def test_perda_aberta_consome_folga():
    pos = [{"ticker": "RADL3", "volume": 1000.0, "preco_atual": 20.0, "lucro": -50.0}]
    r = calcular(_cfg(), CONTA_DEMO, pos, SIMB, SEM_MT5, FORA)
    a = _radl(r)
    assert r["conta"]["patrimonio"] == 4950.0 and r["conta"]["margem_usada"] == 100.0
    assert (a["qtd_carteira"], a["lucro_aberto"], a["folga_perda_ativo"]) == (1000.0, -50.0, 450.0)
    assert r["conta"]["folga_perda_total"] == 950.0
    assert a["lotes_operaveis"] == 5  # 15 − 10 lotes em carteira


def test_lucro_aumenta_folga():
    pos = [{"ticker": "RADL3", "volume": 100.0, "preco_atual": 20.0, "lucro": 50.0}]
    assert _radl(calcular(_cfg(), CONTA_DEMO, pos, SIMB, SEM_MT5, FORA))["folga_perda_ativo"] == 550.0


def test_limite_de_perda_atingido_bloqueia():
    pos = [{"ticker": "RADL3", "volume": 1000.0, "preco_atual": 20.0, "lucro": -500.0}]
    a = _radl(calcular(_cfg(), CONTA_DEMO, pos, SIMB, SEM_MT5, FORA))
    assert (a["lotes_operaveis"], a["restricao"]) == (0, "perda_aberta_ativo")


def test_sem_cotacao_zera():
    r = calcular(_cfg(), CONTA_DEMO, [], SIMB, SEM_MT5, FORA)
    x = r["ativos"][1]
    assert (x["lotes_operaveis"], x["restricao"]) == (0, "sem_cotacao")


def test_fora_universo_ignorada_no_simulado():
    pos = [{"ticker": "WDOG26", "volume": 1.0, "preco_atual": 5230.0, "lucro": 50.0}]
    r = calcular(_cfg(), CONTA_DEMO, pos, SIMB, SEM_MT5, FORA)
    assert r["ignoradas_fora_universo"] == ["WDOG26"] and r["conta"]["patrimonio"] == 5000.0


@pytest.mark.parametrize("capital", [0.0, 5000.0])
def test_real_ou_sem_capital_usa_conta_e_mt5(capital):
    cfg = _cfg()
    cfg.simulacao.capital_simulado = capital
    if capital:
        cfg.geral.ambiente = "real"
    conta = {"saldo": 5000.0, "patrimonio": 5000.0, "margem": 0.0, "margem_livre": 5000.0}
    r = calcular(cfg, conta, [], SIMB, lambda t, v, p: 20.0, FORA)
    assert r["modo"] == "conta" and _radl(r)["margem_lote"] == 20.0


def test_cotacao_parada_no_pregao_zera():
    simb = [{**SIMB[0], "horario_cotacao": "2026-10-19T11:00:00.000"}]
    a = _radl(calcular(_cfg(), CONTA_DEMO, [], simb, SEM_MT5, datetime(2026, 10, 19, 11, 5)))
    assert (a["lotes_operaveis"], a["restricao"]) == (0, "sem_cotacao")
