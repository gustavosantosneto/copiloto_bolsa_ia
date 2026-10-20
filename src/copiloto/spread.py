"""Spread: atual (bid/ask) × média do ativo em ticks (spread M1 das últimas sessões).

Só atenção, nunca decisivo. spread_pct = (ask − bid) / meio × 100; ticks = (ask − bid) / ponto.
Em ticks porque spread B3 é quantizado (quase sempre 1 tick) → desvio padrão fica minúsculo e dispara à toa.
Referência M1 = 1 spread por candle (aproximação). Fora do pregão bid/ask não valem → sem atenção.
"""

from datetime import datetime
from statistics import mean

from copiloto import mercado
from copiloto.config import Config
from copiloto.guardas import em_pregao

_cache: dict[str, tuple[float, dict]] = {}  # ticker → (mtime do CSV, referência)


def spread_pct(s: dict) -> float | None:
    bid, ask = s.get("bid"), s.get("ask")
    if not bid or not ask or ask < bid:
        return None
    return (ask - bid) / ((ask + bid) / 2) * 100


def referencia(cfg: Config, ticker: str) -> dict:
    caminho = mercado.arquivo(cfg, ticker)
    if not caminho.exists():
        return {"n": 0, "media_ticks": None, "media_pct": None}
    mtime = caminho.stat().st_mtime
    if ticker in _cache and _cache[ticker][0] == mtime:
        return _cache[ticker][1]
    c = [x for x in mercado.ler(cfg, ticker, cfg.spread.janela_sessoes) if x["spread_pct"] is not None]
    ref = {"n": len(c), "media_ticks": mean(x["spread_pts"] for x in c) if c else None,
           "media_pct": mean(x["spread_pct"] for x in c) if c else None}
    _cache[ticker] = (mtime, ref)
    return ref


def avaliar(cfg: Config, simbolos: list[dict]) -> list[dict]:
    """Status: teto · anormal · ok · sem_referencia (amostra < min_amostras) · sem_cotacao."""
    sp, saida = cfg.spread, []
    for s in simbolos:
        atual, ref = spread_pct(s), referencia(cfg, s["ticker"])
        ticks = round((s["ask"] - s["bid"]) / s["ponto"], 1) if atual is not None and s.get("ponto") else None
        acima = ticks - ref["media_ticks"] if ticks is not None and ref["media_ticks"] is not None else None
        if atual is None:
            status = "sem_cotacao"
        elif atual > sp.spread_max_pct:
            status = "teto"
        elif ref["n"] < sp.min_amostras or acima is None:
            status = "sem_referencia"
        else:
            status = "anormal" if acima > sp.ticks_acima_media else "ok"
        r = lambda x, c=4: round(x, c) if x is not None else None  # noqa: E731
        saida.append({"ticker": s["ticker"], "spread_pct": r(atual), "spread_ticks": ticks, "media_pct": r(ref["media_pct"]),
                      "media_ticks": r(ref["media_ticks"], 2), "acima_media_ticks": r(acima, 2),
                      "n_amostras": ref["n"], "status": status})
    return saida


def atencoes(cfg: Config, avaliacao: list[dict], agora: datetime) -> list[dict]:
    if not em_pregao(cfg, agora):
        return []
    sp, saida = cfg.spread, []
    for a in avaliacao:
        if a["status"] == "teto":
            saida.append({"tipo": "spread_teto", "ticker": a["ticker"],
                          "msg": f"spread {a['spread_pct']:.3f}% > teto {sp.spread_max_pct}% (custo/risco alto)"})
        elif a["status"] == "anormal":
            saida.append({"tipo": "spread_anormal", "ticker": a["ticker"],
                          "msg": f"spread {a['spread_ticks']:g} ticks > média {a['media_ticks']:.2f} + {sp.ticks_acima_media:g}"})
    return saida
