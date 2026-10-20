"""Diagnóstico das operações encerradas: MAE/MFE (pior/melhor P&L aberto) a partir dos negócios tick a tick.

Operação = ticket_posicao com entrada e saída no CSV de deals. P&L aberto recalculado a cada negócio
com o preço médio e o volume da posição naquele instante (entradas/saídas parciais incluídas).
Limites: preço = último negócio (não bid/ask), sem custos; posição com inversão é ignorada. Histórico ≠ previsão.
"""

from statistics import median

from copiloto import negocios
from copiloto.config import Config

ENTRADA, SAIDAS = "entrada", {"saida", "saida_por"}
FOLGA_MS = 5 * 60_000  # sem negócio até 5 min da entrada/saída → ticks não cobrem a operação (rodar `copiloto mercado`)


def operacoes(deals: list[dict]) -> list[list[dict]]:
    """Agrupa deals por posição (ordem de tempo); só posições encerradas e completas no CSV."""
    por_pos: dict[int, list[dict]] = {}
    for d in sorted(deals, key=lambda d: d["data_hora"]):
        por_pos.setdefault(d["ticket_posicao"], []).append(d)
    saida = []
    for ds in por_pos.values():
        entrou = sum(d["qtd"] for d in ds if d["entrada"] == ENTRADA)
        saiu = sum(d["qtd"] for d in ds if d["entrada"] in SAIDAS)
        if ds[0]["entrada"] == ENTRADA and entrou and entrou == saiu and not any(d["entrada"] == "inversao" for d in ds):
            saida.append(ds)
    return saida


def excursao(op: list[dict], ticks: list[tuple]) -> dict:
    """MAE/MFE em R$ sobre o P&L aberto; tempo (min) desde a 1ª entrada."""
    sinal = 1 if op[0]["tipo"] == "compra" else -1
    eventos = [(negocios.ms(d["data_hora"]), d) for d in op]
    t0 = eventos[0][0]
    vol = pm = qtd_max = 0.0
    mae = mfe = 0.0
    t_mae = t_mfe = t0
    i = 0
    for t, _bid, _ask, ultimo, _v, _f in ticks:
        while i < len(eventos) and eventos[i][0] <= t:
            d = eventos[i][1]
            if d["entrada"] == ENTRADA:
                pm = (pm * vol + d["preco"] * d["qtd"]) / (vol + d["qtd"])
                vol += d["qtd"]
                qtd_max = max(qtd_max, vol)
            else:
                vol -= d["qtd"]
            i += 1
        if vol > 0:
            pnl = (ultimo - pm) * vol * sinal
            if pnl < mae:
                mae, t_mae = pnl, t
            if pnl > mfe:
                mfe, t_mfe = pnl, t
    return {"mae": mae, "mfe": mfe, "min_ate_mae": (t_mae - t0) / 60_000, "min_ate_mfe": (t_mfe - t0) / 60_000,
            "qtd_max": qtd_max, "pm": pm}


def calcular(cfg: Config, deals: list[dict]) -> dict:
    ops, linhas = operacoes(deals), []
    with negocios.conectar(cfg) as con:
        for op in ops:
            ini, fim = negocios.ms(op[0]["data_hora"]), negocios.ms(op[-1]["data_hora"])
            ticks = negocios.ler(con, op[0]["ticker"], ini, fim)
            base = {"ticker": op[0]["ticker"], "lado": op[0]["tipo"], "abertura": op[0]["data_hora"],
                    "fechamento": op[-1]["data_hora"], "duracao_min": round((fim - ini) / 60_000, 1),
                    "resultado_bruto": round(sum(d["resultado_bruto"] or 0 for d in op), 2),
                    "motivo_saida": op[-1].get("motivo") or None,
                    "entradas": sum(d["entrada"] == ENTRADA for d in op), "saidas": sum(d["entrada"] in SAIDAS for d in op)}
            if not ticks or ticks[0][0] > ini + FOLGA_MS or ticks[-1][0] < fim - FOLGA_MS:
                linhas.append(base | {"status": "sem_ticks"})
                continue
            e = excursao(op, ticks)
            valor = e["pm"] * e["qtd_max"]
            linhas.append(base | {
                "status": "ok", "qtd_max": e["qtd_max"], "mae": round(e["mae"], 2), "mfe": round(e["mfe"], 2),
                "mae_pct": round(e["mae"] / valor * 100, 3) if valor else None,
                "mfe_pct": round(e["mfe"] / valor * 100, 3) if valor else None,
                "min_ate_mae": round(e["min_ate_mae"], 1), "min_ate_mfe": round(e["min_ate_mfe"], 1),
                "captura_pct": round(base["resultado_bruto"] / e["mfe"] * 100, 1) if e["mfe"] > 0 else None,
            })
    return {"resumo": resumo(linhas), "operacoes": linhas[::-1]}  # mais recente primeiro


def _q(v: list[float], p: float) -> float | None:
    if not v:
        return None
    s = sorted(v)
    return round(s[min(len(s) - 1, int(p * len(s)))], 2)


def resumo(linhas: list[dict]) -> dict:
    ok = [l for l in linhas if l["status"] == "ok"]
    mae = [l["mae"] for l in ok]
    grupos: dict[str, list[dict]] = {}
    for l in ok:
        grupos.setdefault(l["motivo_saida"] or "?", []).append(l)
    return {
        "operacoes": len(linhas), "com_ticks": len(ok), "sem_ticks": len(linhas) - len(ok),
        "periodo": [linhas[0]["abertura"][:10], linhas[-1]["fechamento"][:10]] if linhas else None,
        "mae_mediana": _q(mae, 0.5), "mae_p10": _q(mae, 0.1), "mae_pior": min(mae) if mae else None,
        "mfe_mediana": _q([l["mfe"] for l in ok], 0.5),
        "captura_mediana_pct": _q([l["captura_pct"] for l in ok if l["captura_pct"] is not None], 0.5),
        "duracao_mediana_min": round(median(l["duracao_min"] for l in ok), 1) if ok else None,
        "por_motivo": {m: {"n": len(g), "resultado_medio": round(sum(x["resultado_bruto"] for x in g) / len(g), 2),
                           "mae_mediana": _q([x["mae"] for x in g], 0.5)} for m, g in grupos.items()},
        "limites": "demo; preço = último negócio; sem custos; amostra pequena → não generalizar",
    }
