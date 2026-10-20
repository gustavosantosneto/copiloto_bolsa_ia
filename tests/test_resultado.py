"""Resultado: custo MT5 > estimativa B3; day trade por posição/dia; drawdown só realizado."""

from copiloto.config import carregar_config
from copiloto.resultado import calcular, custo_deal

CFG = carregar_config()


def _d(hora, entrada, pos=1, bruto=0.0, custos=0.0):
    return {"data_hora": hora, "entrada": entrada, "ticket_posicao": pos, "resultado_bruto": bruto,
            "qtd": 100.0, "preco": 20.0, "custos": custos}


def test_custo_mt5_tem_prioridade_senao_estima_b3():
    assert custo_deal(CFG, _d("x", "entrada", custos=-1.5), True) == 1.5
    assert round(custo_deal(CFG, _d("x", "entrada"), True), 4) == 0.46  # 2000 × 0,023%
    assert round(custo_deal(CFG, _d("x", "entrada"), False), 4) == 0.6  # 2000 × 0,030%


def test_day_trade_por_posicao_e_dia():
    ds = [_d("2026-10-19T10:00", "entrada", 1), _d("2026-10-19T11:00", "saida", 1, bruto=50.0),
          _d("2026-10-19T12:00", "entrada", 2)]  # posição 2 segue aberta → swing
    t = calcular(CFG, ds)["total"]
    assert (t["custos"], t["operacoes"], t["liquido"]) == (1.52, 1, 48.48)
    assert t["ganho_medio_operacao"] == 48.48


def test_drawdown_e_por_dia():
    ds = [_d("2026-10-19T10:00", "saida", 1, bruto=100.0), _d("2026-10-19T11:00", "saida", 2, bruto=-60.0),
          _d("2026-10-20T10:00", "saida", 3, bruto=-20.0)]
    r = calcular(CFG, ds)
    assert (r["total"]["drawdown_max"], r["total"]["drawdown_atual"]) == (81.2, 81.2)  # pico 99,4 → 18,2
    assert [d["dia"] for d in r["por_dia"]] == ["2026-10-20", "2026-10-19"]
    assert (r["total"]["dias"], r["total"]["ganho_medio_dia"]) == (2, 9.1)
