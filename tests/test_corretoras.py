"""Corretoras: matriz > padrão; sem dado → 0 lotes; linha vencida ignorada; custo ida+volta."""

from datetime import datetime

from copiloto.config import carregar_config
from copiloto.corretoras import custo_operacao, simular

CFG = carregar_config()
CONTA = {"saldo": 1_000_000.0, "patrimonio": 1_000_000.0, "margem": 0.0, "margem_livre": 1_000_000.0}
SIMB = [{"ticker": "ABEV3", "existe": True, "ask": 15.0, "ultimo": 15.0},
        {"ticker": "B3SA3", "existe": True, "ask": 12.0, "ultimo": 12.0}]
NOITE = datetime(2026, 10, 20, 20, 0)


def test_matriz_sobrepoe_padrao_e_sem_dado_zera():
    r = {c["corretora"]: c for c in simular(CFG, CONTA, [], SIMB, NOITE)}
    clear = {a["ticker"]: a for a in r["Clear"]["ativos"]}
    assert clear["ABEV3"]["alavancagem"] == 200 and clear["ABEV3"]["origem"].startswith("matriz")
    assert (clear["B3SA3"]["alavancagem"], clear["B3SA3"]["margem_lote"]) == (35, 34.29)
    assert r["Toro"]["ativos"][0]["lotes_operaveis"] == 0


def test_linha_vencida_ignorada():
    assert simular(CFG, CONTA, [], SIMB, datetime(2027, 1, 1, 20, 0)) == []


def test_custo_operacao_ida_volta():
    assert custo_operacao(CFG, 1500.0, 0.0) == 0.69  # 2 × 1500 × 0,023%
