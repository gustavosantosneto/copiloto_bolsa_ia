"""Atenções de limite de risco ([risco]) e divergência de margem. Só apoio, nunca decisivo; nada é enviado.

Base = conta usada nos cálculos (capacidade: simulada na demo). Perda do dia = realizado líquido hoje + P&L aberto.
Saldo início do dia = saldo − realizado MT5 hoje (simulado: capital fixo).
"""

from copiloto import medicao, resultado
from copiloto.config import Config


def limites(cfg: Config, cap: dict, posicoes: list[dict], deals_hoje: list[dict]) -> list[dict]:
    r, c = cfg.risco, cap["conta"]
    atencoes = []

    def atencao(tipo: str, msg: str, **extra):
        atencoes.append({"tipo": tipo, **extra, "msg": msg})

    realizado_mt5 = sum(d["resultado_liquido"] or 0 for d in deals_hoje)  # já está no saldo da conta
    saldo_inicio = c["saldo"] - (realizado_mt5 if cap["modo"] == "conta" else 0)
    perda_dia = resultado.calcular(cfg, deals_hoje)["total"]["liquido"] + c["patrimonio"] - c["saldo"]
    limite_dia = r.perda_max_dia / 100 * saldo_inicio
    if perda_dia <= -limite_dia:
        atencao("perda_max_dia", f"perda do dia R$ {-perda_dia:.2f} ≥ limite R$ {limite_dia:.2f} ({r.perda_max_dia}% do saldo inicial)")

    universo = {a["ticker"] for a in cap["ativos"]}
    for p in posicoes:
        if p["lucro"] <= -r.perda_max_operacao and (cap["modo"] == "conta" or p["ticker"] in universo):
            atencao("perda_max_operacao", f"P&L aberto R$ {p['lucro']:.2f} ≤ −R$ {r.perda_max_operacao:.2f}",
                   ticker=p["ticker"])
    for a in cap["ativos"]:
        if a["folga_perda_ativo"] <= 0:
            atencao("perda_aberta_ativo", f"perda aberta passou do limite do ativo (R$ {c['limite_perda_ativo']:.2f})",
                   ticker=a["ticker"])
    if c["folga_perda_total"] <= 0:
        atencao("perda_aberta_total", f"perda aberta total passou do limite ({r.perda_aberta_max_total_pct}% do saldo)")

    if c["margem_usada"] > 0:
        if c["margem_usada"] > r.margem_usada_max_pct / 100 * c["patrimonio"]:
            atencao("margem_usada_max", f"margem usada R$ {c['margem_usada']:.2f} > {r.margem_usada_max_pct}% do patrimônio")
        nivel = c["patrimonio"] / c["margem_usada"] * 100
        if nivel < r.nivel_margem_min_pct:
            atencao("nivel_margem_min", f"nível de margem {nivel:.0f}% < {r.nivel_margem_min_pct:.0f}%")

    for m in medicao.divergentes(cfg, deals_hoje):
        atencao("divergencia_margem", f"Δmargem R$ {m['delta_margem']:.2f} × prevista MT5 R$ {m['margem_prevista_mt5']:.2f} "
                                     f"({m['divergencia_pct']:.1f}%)", ticker=m["ticker"], horario=m["data_hora"])
    return atencoes
