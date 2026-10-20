"""Base operacional: margem/alavancagem medidas por ativo a partir dos deals com snapshot (docs/OPERACIONAL.md §3).

Medição = deal do coletor sozinho no ciclo (deals_no_ciclo=1) com Δmargem ≠ 0.
Δmargem inclui reprecificação das outras posições no mesmo ciclo (≤1 s) → erro pequeno, aceito.
"""

import csv
from pathlib import Path
from statistics import median

from copiloto.config import Config
from copiloto.registro import arquivo, ler

COLUNAS_BASE = [
    "ticker", "n_medicoes", "margem_por_lote", "alavancagem_medida", "alavancagem_min", "alavancagem_max",
    "divergencia_mt5_max_pct", "primeira_medicao", "ultima_medicao", "ambiente", "status",
]


def medicoes(cfg: Config, deals: list[dict]) -> list[dict]:
    """1 medição por deal válido, ordem cronológica."""
    lote, saida = cfg.operacao.lote_padrao, []
    for d in sorted(deals, key=lambda d: d["data_hora"]):
        if d["fonte"] != "coletor" or d["deals_no_ciclo"] != 1 or d["margem_antes"] is None or d["margem_depois"] is None:
            continue
        delta = abs(d["margem_depois"] - d["margem_antes"])
        if not delta or not d["qtd"]:
            continue
        prev = d["margem_prevista_mt5"]
        saida.append({
            "data_hora": d["data_hora"], "ticker": d["ticker"], "qtd": d["qtd"], "preco": d["preco"],
            "delta_margem": round(delta, 2), "margem_por_lote": round(delta / (d["qtd"] / lote), 2),
            "alavancagem_medida": round(d["qtd"] * d["preco"] / delta, 1), "margem_prevista_mt5": prev,
            "divergencia_pct": round(abs(delta - prev) / prev * 100, 2) if prev else None, "ambiente": d["ambiente"],
        })
    return saida


def divergentes(cfg: Config, deals: list[dict]) -> list[dict]:
    """Medições cuja Δmargem diverge do previsto MT5 além da tolerância."""
    r = cfg.registro
    if not r.comparar_margem_prevista:
        return []
    return [m for m in medicoes(cfg, deals)
            if m["divergencia_pct"] is not None and m["divergencia_pct"] > r.tolerancia_divergencia_margem_pct]


def consolidar(cfg: Config, deals: list[dict]) -> list[dict]:
    """1 linha por ativo (mediana). Menos que min_medicoes_margem_validada → status pendente."""
    por_ticker: dict[str, list[dict]] = {}
    for m in medicoes(cfg, deals):
        por_ticker.setdefault(m["ticker"], []).append(m)
    base = []
    for t, ms in sorted(por_ticker.items()):
        alav = [m["alavancagem_medida"] for m in ms]
        div = [m["divergencia_pct"] for m in ms if m["divergencia_pct"] is not None]
        base.append({
            "ticker": t, "n_medicoes": len(ms), "margem_por_lote": round(median(m["margem_por_lote"] for m in ms), 2),
            "alavancagem_medida": round(median(alav), 1), "alavancagem_min": min(alav), "alavancagem_max": max(alav),
            "divergencia_mt5_max_pct": max(div) if div else None,
            "primeira_medicao": ms[0]["data_hora"], "ultima_medicao": ms[-1]["data_hora"],
            "ambiente": "/".join(sorted({m["ambiente"] for m in ms})),
            "status": "observado" if len(ms) >= cfg.registro.min_medicoes_margem_validada else "pendente",
        })
    return base


def gravar_base(cfg: Config, conta: int | None = None) -> Path:
    """Regera dados/{conta}_base_operacional.csv a partir do histórico da conta."""
    destino = arquivo(cfg, "csv_base_operacional", conta)
    base = consolidar(cfg, ler(cfg, None, arquivo(cfg, "csv_historico", conta)))
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLUNAS_BASE, delimiter=";")
        w.writeheader()
        w.writerows(base)
    return destino
