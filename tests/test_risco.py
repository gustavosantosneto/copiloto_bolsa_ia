"""Limites de risco: perda do dia (realizado + aberto), por operação, folgas, margem."""

from copiloto.config import carregar_config
from copiloto.risco import limites

CFG = carregar_config()


def _cap(patrimonio=5000.0, margem=0.0, folga_ativo=500.0, folga_total=1000.0):
    return {"modo": "simulado", "conta": {"saldo": 5000.0, "patrimonio": patrimonio, "margem_usada": margem,
                                          "limite_perda_ativo": 500.0, "folga_perda_total": folga_total},
            "ativos": [{"ticker": "RADL3", "folga_perda_ativo": folga_ativo}]}


def _tipos(atencoes):
    return [a["tipo"] for a in atencoes]


def test_tudo_normal():
    assert limites(CFG, _cap(margem=10.0), [], []) == []


def test_perda_dia_soma_realizado_e_aberto():
    deal = {"data_hora": "2026-10-20T10:00", "entrada": "saida", "ticket_posicao": 1, "resultado_bruto": -600.0,
            "qtd": 100.0, "preco": 20.0, "custos": -1.0, "resultado_liquido": -601.0, "fonte": "mt5_historico"}
    assert _tipos(limites(CFG, _cap(patrimonio=4600.0), [], [deal])) == ["perda_max_dia"]  # −601 − 400 ≥ 20% de 5000


def test_operacao_folgas_e_margem():
    a = limites(CFG, _cap(margem=1500.0, folga_ativo=0.0, folga_total=-1.0), [{"ticker": "RADL3", "lucro": -250.0}], [])
    assert _tipos(a) == ["perda_max_operacao", "perda_aberta_ativo", "perda_aberta_total", "margem_usada_max",
                         "nivel_margem_min"]
