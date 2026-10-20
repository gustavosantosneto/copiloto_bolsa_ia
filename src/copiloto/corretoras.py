"""Corretoras: cadastro, matriz margem ativo × corretora, custo efetivo e capacidade simulada por corretora.

Valor público = teto declarado, não garantia (docs/CONTEXTO.md). Linha vencida (valido_ate < hoje) é ignorada.
Alavancagem do ativo: matriz → senão alavancagem_padrao_dt da corretora → senão sem dado (0 lotes).
"""

import csv
from datetime import datetime

from copiloto.capacidade import calcular
from copiloto.config import RAIZ, Config


def _ler(cfg: Config, chave: str, hoje: str) -> list[dict]:
    with open(RAIZ / getattr(cfg.registro, chave), newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f, delimiter=";") if not r["valido_ate"] or r["valido_ate"] >= hoje]


def _num(v: str) -> float | None:
    return float(v) if v else None


def custo_operacao(cfg: Config, valor: float, corretagem: float | None, day_trade: bool = True) -> float:
    """Ida + volta: emolumentos B3 nas duas pontas + 2 corretagens."""
    op = cfg.operacao
    pct = op.emolumentos_day_trade_pct if day_trade else op.emolumentos_swing_pct
    return round(2 * valor * pct / 100 + 2 * (corretagem or 0), 2)


def simular(cfg: Config, conta: dict, posicoes: list[dict], simbolos: list[dict], agora: datetime | None = None) -> list[dict]:
    """Capacidade de cada corretora com a alavancagem dela (mesmos limites de [risco]); custo DT de 1 lote."""
    hoje = (agora or datetime.now()).date().isoformat()
    matriz = {(m["corretora"], m["ticker"]): m for m in _ler(cfg, "csv_margens_corretora", hoje)}
    cfg_sim = cfg.model_copy(deep=True)
    cfg_sim.simulacao.alavancagem_simulada = 0  # margem vem da corretora, não da simulação
    saida = []
    for c in _ler(cfg, "csv_corretoras", hoje):
        nome, padrao = c["corretora"], _num(c["alavancagem_padrao_dt"])

        def alav(t: str) -> tuple[float | None, str]:
            m = matriz.get((nome, t))
            return (float(m["alavancagem"]), f"matriz {m['status']}") if m else (padrao, f"padrao {c['status']}")

        cap = calcular(cfg_sim, conta, posicoes, simbolos,
                       lambda t, v, p: p * v / a if (a := alav(t)[0]) else None, agora)
        corretagem = _num(c["corretagem_day_trade"])
        saida.append({
            "corretora": nome, "alavancagem_max_dt": _num(c["alavancagem_max_dt"]), "alavancagem_padrao_dt": padrao,
            "corretagem_day_trade": corretagem, "plataforma_mt5": c["plataforma_mt5"] or None, "regra": c["regra"],
            "fonte": c["fonte"], "url": c["url"], "data": c["data"], "valido_ate": c["valido_ate"], "status": c["status"],
            "ativos": [{"ticker": a["ticker"], "alavancagem": alav(a["ticker"])[0], "origem": alav(a["ticker"])[1],
                        "margem_lote": a.get("margem_lote"), "lotes_operaveis": a["lotes_operaveis"],
                        "restricao": a["restricao"],
                        "custo_lote_day_trade": custo_operacao(cfg, a["valor_lote"], corretagem) if "valor_lote" in a else None}
                       for a in cap["ativos"]],
        })
    return saida
