"""Candles p/ estudo → data/mercado/{timeframe}_{ticker}.csv. Incremental: só busca depois do último candle gravado.

Dado de mercado = estudo/fixture, nunca sinal (CLAUDE.md). Candle em formação não é gravado.
spread_pct = spread_pts × ponto / fechamento × 100 (MT5 guarda 1 spread por candle).
"""

import csv
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path

from copiloto.config import RAIZ, Config

COLUNAS = ["data_hora", "abertura", "maxima", "minima", "fechamento", "volume_ticks", "volume_real", "spread_pts",
           "spread_pct"]
MINUTOS = {"M": 1, "H": 60, "D": 1440, "W": 10080}


def arquivo(cfg: Config, ticker: str) -> Path:
    return RAIZ / cfg.mercado.pasta / f"{cfg.mercado.timeframe}_{ticker}.csv"


def _duracao(tf: str) -> timedelta:
    return timedelta(minutes=MINUTOS[tf[0]] * int(tf[1:] or 1)) if tf != "MN1" else timedelta(days=31)


def _primeiro(caminho: Path) -> str | None:
    if not caminho.exists():
        return None
    with open(caminho, encoding="utf-8") as f:
        f.readline()
        h = f.readline().split(";", 1)[0]
    return h or None


def _linha(v: dict, ponto: float) -> dict:
    return {"data_hora": v["horario"], **{k: v[k] for k in COLUNAS[1:-1]},
            "spread_pct": round(v["spread_pts"] * ponto / v["fechamento"] * 100, 4) if v["fechamento"] else ""}


def _completar_inicio(servico, caminho: Path, t: str, inicio: datetime, ponto: float) -> int:
    """Arquivo começa depois de `inicio` (dias_iniciais aumentou) → busca o trecho anterior e reescreve com ele na frente."""
    primeiro = _primeiro(caminho)
    if not primeiro or datetime.fromisoformat(primeiro) - inicio < timedelta(days=1):
        return 0
    velas = [v for v in servico.candles(t, inicio, datetime.fromisoformat(primeiro)) if v["horario"] < primeiro]
    if not velas:
        return 0
    with open(caminho, newline="", encoding="utf-8") as f:
        f.readline()  # cabeçalho
        antigo = f.read()
    tmp = caminho.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLUNAS, delimiter=";")
        w.writeheader()
        w.writerows(_linha(v, ponto) for v in velas)
        f.write(antigo)
    tmp.replace(caminho)
    return len(velas)


def _ultimo(caminho: Path) -> str | None:
    if not caminho.exists():
        return None
    with open(caminho, encoding="utf-8") as f:
        linha = deque(f, 1)
    h = linha[0].split(";", 1)[0] if linha else ""
    return h if h and h != "data_hora" else None


def atualizar(servico, cfg: Config, agora: datetime | None = None) -> dict[str, int | str]:
    """Watchlist: 1ª vez = dias_iniciais; depois só o que falta (no fim e, se dias_iniciais aumentou, no início)."""
    m, agora = cfg.mercado, agora or datetime.now()  # servidor XP = horário local
    (RAIZ / m.pasta).mkdir(parents=True, exist_ok=True)
    pontos = {s["ticker"]: s.get("ponto") for s in servico.simbolos()}
    dur, saida = _duracao(m.timeframe), {}
    for t in cfg.universo.watchlist:
        if not pontos.get(t):
            saida[t] = "símbolo inexistente"
            continue
        caminho, inicio = arquivo(cfg, t), agora - timedelta(days=m.dias_iniciais)
        antes = _completar_inicio(servico, caminho, t, inicio, pontos[t])
        ultimo = _ultimo(caminho)
        desde = datetime.fromisoformat(ultimo) + dur if ultimo else inicio
        velas = [v for v in servico.candles(t, desde, agora)
                 if (not ultimo or v["horario"] > ultimo) and datetime.fromisoformat(v["horario"]) + dur <= agora]
        novo = not caminho.exists()
        with open(caminho, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, COLUNAS, delimiter=";")
            if novo:
                w.writeheader()
            w.writerows(_linha(v, pontos[t]) for v in velas)
        saida[t] = len(velas) + antes
    return saida


def ler(cfg: Config, ticker: str, sessoes: int | None = None) -> list[dict]:
    """Candles gravados (números convertidos); `sessoes` = só os últimos N dias com pregão."""
    caminho = arquivo(cfg, ticker)
    if not caminho.exists():
        return []
    with open(caminho, newline="", encoding="utf-8") as f:
        linhas = [{k: (v if k == "data_hora" else float(v) if v else None) for k, v in r.items()}
                  for r in csv.DictReader(f, delimiter=";")]
    if sessoes:
        dias = sorted({r["data_hora"][:10] for r in linhas})[-sessoes:]
        linhas = [r for r in linhas if r["data_hora"][:10] >= dias[0]] if dias else []
    return linhas
