"""Capacidade operacional: lotes padrão operáveis por ativo (só cálculo, nada é enviado).

Lotes = menor entre margem livre, teto de margem usada e máx. posições. `restricao` diz qual travou.
Perda aberta: limite (% do saldo) − perda atual = folga p/ cair. Folga ≤ 0 → 0 lotes (ativo ou total).
Demo + simulacao.capital_simulado > 0 → conta simulada (saldo = capital; margem = valor/alavancagem).
"""

import math
from collections.abc import Callable

from copiloto.config import Config


def _lotes(disponivel: float, por_lote: float) -> int:
    return max(0, math.floor(disponivel / por_lote)) if por_lote > 0 else 0


def calcular(cfg: Config, conta: dict, posicoes: list[dict], simbolos: list[dict],
             margem_prevista: Callable[[str, float, float], float | None]) -> dict:
    sim, lote = cfg.simulacao, cfg.operacao.lote_padrao
    simulado = cfg.geral.ambiente == "demo" and sim.capital_simulado > 0
    universo = {s["ticker"] for s in simbolos}
    consideradas = [p for p in posicoes if p["ticker"] in universo] if simulado else posicoes
    lucro = {p["ticker"]: 0.0 for p in consideradas}
    for p in consideradas:
        lucro[p["ticker"]] += p["lucro"]

    def margem_lote(ticker: str, preco: float) -> float | None:
        if simulado and sim.alavancagem_simulada > 0:
            return preco * lote / sim.alavancagem_simulada
        return margem_prevista(ticker, lote, preco)

    if simulado:
        saldo = sim.capital_simulado
        patrimonio = saldo + sum(lucro.values())
        margem_usada = sum((margem_lote(p["ticker"], p["preco_atual"]) or 0) * p["volume"] / lote for p in consideradas)
        margem_livre = patrimonio - margem_usada
    else:
        saldo, patrimonio = conta["saldo"], conta["patrimonio"]
        margem_usada, margem_livre = conta["margem"], conta["margem_livre"]

    r = cfg.risco
    teto_margem = r.margem_usada_max_pct / 100 * patrimonio - margem_usada
    limite_ativo = r.perda_aberta_max_ativo_pct / 100 * saldo
    limite_total = r.perda_aberta_max_total_pct / 100 * saldo
    folga_total = limite_total + sum(lucro.values())  # lucro negativo consome folga
    lotado = len(lucro) >= r.max_posicoes_abertas

    ativos = []
    for s in simbolos:
        t = s["ticker"]
        preco = (s.get("ask") or s.get("ultimo")) if s.get("existe") else None
        folga_ativo = limite_ativo + lucro.get(t, 0.0)
        linha = {"ticker": t, "preco": preco, "qtd_carteira": sum(p["volume"] for p in consideradas if p["ticker"] == t),
                 "lucro_aberto": round(lucro.get(t, 0.0), 2), "folga_perda_ativo": round(folga_ativo, 2)}
        ml = margem_lote(t, preco) if preco else None
        if not preco or not ml:
            ativos.append(linha | {"lotes_operaveis": 0, "restricao": "sem_cotacao" if not preco else "sem_margem"})
            continue
        limites = {"margem_livre": _lotes(margem_livre, ml), "margem_usada_max": _lotes(teto_margem, ml)}
        if lotado and t not in lucro:
            limites["max_posicoes"] = 0
        if folga_ativo <= 0:
            limites["perda_aberta_ativo"] = 0
        if folga_total <= 0:
            limites["perda_aberta_total"] = 0
        restricao = min(limites, key=lambda k: limites[k])
        ativos.append(linha | {"valor_lote": round(preco * lote, 2), "margem_lote": round(ml, 2),
                               "alavancagem_lote": round(preco * lote / ml, 1),
                               "lotes_por_limite": limites, "lotes_operaveis": limites[restricao],
                               "restricao": restricao})

    return {
        "modo": "simulado" if simulado else "conta",
        "conta": {"saldo": round(saldo, 2), "patrimonio": round(patrimonio, 2), "margem_usada": round(margem_usada, 2),
                  "margem_livre": round(margem_livre, 2), "limite_perda_ativo": round(limite_ativo, 2),
                  "folga_perda_total": round(folga_total, 2)},
        "ignoradas_fora_universo": sorted({p["ticker"] for p in posicoes} - universo) if simulado else [],
        "ativos": ativos,
    }
