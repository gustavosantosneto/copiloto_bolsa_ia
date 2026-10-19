"""Capacidade operacional: lotes padrão operáveis por ativo (só cálculo, nada é enviado).

Cada limite vira um nº de lotes; operável = menor deles. `restricao` diz qual travou.
Demo + simulacao.capital_simulado > 0 → conta simulada (capital + P&L aberto; margem = valor/alavancagem).
"""

import math
from collections.abc import Callable

from copiloto.config import Config


def _lotes(disponivel: float, por_lote: float) -> int:
    return max(0, math.floor(disponivel / por_lote)) if por_lote > 0 else 0


def calcular(cfg: Config, conta: dict, posicoes: list[dict], simbolos: list[dict],
             margem_prevista: Callable[[str, float, float], float | None]) -> dict:
    sim = cfg.simulacao
    simulado = cfg.geral.ambiente == "demo" and sim.capital_simulado > 0
    universo = {s["ticker"] for s in simbolos}
    consideradas = [p for p in posicoes if p["ticker"] in universo] if simulado else posicoes
    valor = {p["ticker"]: 0.0 for p in consideradas}
    for p in consideradas:
        valor[p["ticker"]] += p["volume"] * p["preco_atual"]
    valor_total = sum(valor.values())

    def margem_lote(ticker: str, preco: float) -> float | None:
        if simulado and sim.alavancagem_simulada > 0:
            return preco * cfg.operacao.lote_padrao / sim.alavancagem_simulada
        return margem_prevista(ticker, cfg.operacao.lote_padrao, preco)

    if simulado:
        patrimonio = sim.capital_simulado + sum(p["lucro"] for p in consideradas)
        margem_usada = sum((margem_lote(p["ticker"], p["preco_atual"]) or 0) * p["volume"] / cfg.operacao.lote_padrao
                           for p in consideradas)
        margem_livre = patrimonio - margem_usada
    else:
        patrimonio, margem_usada, margem_livre = conta["patrimonio"], conta["margem"], conta["margem_livre"]

    r = cfg.risco
    teto_margem = r.margem_usada_max_pct / 100 * patrimonio - margem_usada
    teto_total = r.exposicao_max_total_pct / 100 * patrimonio - valor_total
    teto_ativo = r.exposicao_max_ativo_pct / 100 * patrimonio
    lotado = len({p["ticker"] for p in consideradas}) >= r.max_posicoes_abertas

    ativos = []
    for s in simbolos:
        t = s["ticker"]
        preco = (s.get("ask") or s.get("ultimo")) if s.get("existe") else None
        linha = {"ticker": t, "preco": preco,
                 "qtd_carteira": sum(p["volume"] for p in consideradas if p["ticker"] == t)}
        ml = margem_lote(t, preco) if preco else None
        if not preco or not ml:
            ativos.append(linha | {"lotes_operaveis": 0, "restricao": "sem_cotacao" if not preco else "sem_margem"})
            continue
        valor_lote = preco * cfg.operacao.lote_padrao
        limites = {
            "margem_livre": _lotes(margem_livre, ml),
            "margem_usada_max": _lotes(teto_margem, ml),
            "exposicao_ativo": _lotes(teto_ativo - valor.get(t, 0.0), valor_lote),
            "exposicao_total": _lotes(teto_total, valor_lote),
        }
        if lotado and t not in valor:
            limites["max_posicoes"] = 0
        restricao = min(limites, key=lambda k: limites[k])
        ativos.append(linha | {"valor_lote": round(valor_lote, 2), "margem_lote": round(ml, 2),
                               "alavancagem_lote": round(valor_lote / ml, 1),
                               "lotes_por_limite": limites, "lotes_operaveis": limites[restricao],
                               "restricao": restricao})

    return {
        "modo": "simulado" if simulado else "conta",
        "conta": {"patrimonio": round(patrimonio, 2), "margem_usada": round(margem_usada, 2),
                  "margem_livre": round(margem_livre, 2), "valor_posicoes": round(valor_total, 2)},
        "ignoradas_fora_universo": sorted({p["ticker"] for p in posicoes} - universo) if simulado else [],
        "ativos": ativos,
    }
