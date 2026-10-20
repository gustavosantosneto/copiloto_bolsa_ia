"""Resultado realizado: bruto, custos, líquido, stats por dia, drawdown. Fonte: CSV de deals da conta.

Custo do deal: MT5 lançou custo (comissão/taxa/swap) → usa; senão estima emolumentos B3 (% por lado) + corretagem.
Day trade = posição com entrada e saída no mesmo dia (taxa DT nas duas pontas); resto = swing.
"""

from copiloto.config import Config

ENTRADAS = {"entrada", "inversao"}
SAIDAS = {"saida", "saida_por", "inversao"}


def _day_trade(deals: list[dict]) -> set[tuple]:
    chave = lambda d: (d["ticket_posicao"], d["data_hora"][:10])  # noqa: E731
    return {chave(d) for d in deals if d["entrada"] in ENTRADAS} & {chave(d) for d in deals if d["entrada"] in SAIDAS}


def custo_deal(cfg: Config, d: dict, day_trade: bool) -> float:
    """Custo em R$ (positivo)."""
    if d["custos"]:
        return -d["custos"]  # MT5: custo vem negativo
    op = cfg.operacao
    pct = op.emolumentos_day_trade_pct if day_trade else op.emolumentos_swing_pct
    return d["qtd"] * d["preco"] * pct / 100 + op.corretagem


def _resumo(deals: int, operacoes: int, bruto: float, custos: float) -> dict:
    n, liquido = operacoes, bruto - custos
    return {"deals": deals, "operacoes": n, "bruto": round(bruto, 2), "custos": round(custos, 2),
            "liquido": round(liquido, 2), "ganho_medio_operacao": round(liquido / n, 2) if n else None,
            "custo_medio_operacao": round(custos / n, 2) if n else None}


def calcular(cfg: Config, deals: list[dict]) -> dict:
    """Operação = posição com saída no dia. Drawdown sobre o líquido acumulado deal a deal (só realizado)."""
    ordenados = sorted(deals, key=lambda d: d["data_hora"])
    dt = _day_trade(ordenados)
    dias: dict[str, dict] = {}
    acumulado = pico = dd_max = 0.0
    for d in ordenados:
        dia = d["data_hora"][:10]
        custo = custo_deal(cfg, d, (d["ticket_posicao"], dia) in dt)
        bruto = d["resultado_bruto"] or 0.0
        x = dias.setdefault(dia, {"dia": dia, "deals": 0, "posicoes": set(), "bruto": 0.0, "custos": 0.0})
        x["deals"] += 1
        x["bruto"] += bruto
        x["custos"] += custo
        if d["entrada"] in SAIDAS:
            x["posicoes"].add(d["ticket_posicao"])
        acumulado += bruto - custo
        pico = max(pico, acumulado)
        dd_max = max(dd_max, pico - acumulado)

    por_dia = [{"dia": x["dia"]} | _resumo(x["deals"], len(x["posicoes"]), x["bruto"], x["custos"]) for x in dias.values()]
    total = _resumo(*(sum(x[k] for x in por_dia) for k in ("deals", "operacoes", "bruto", "custos")))
    total |= {"dias": len(por_dia), "ganho_medio_dia": round(total["liquido"] / len(por_dia), 2) if por_dia else None,
              "drawdown_max": round(dd_max, 2), "drawdown_atual": round(pico - acumulado, 2)}
    return {"total": total, "por_dia": por_dia[::-1]}  # dia mais recente primeiro
