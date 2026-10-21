"""Estudo: similaridade pelo "ângulo" do preço médio de cada minuto ponderado pelo volume (VWAP de 1 minuto).

Fonte padrão = negócios tick a tick: VWAP_min = Σ(preço × volume) / Σvolume dos negócios daquele minuto (exato).
Alternativa sem ticks = preço de 4 pesos do candle M1: (O + H + L + C) / 4.
Ângulo_t = ln(P_t / P_t−1) em bps/min (normalizado: compara ativos de preços diferentes); minuto sem negócio = preço parado.
Medidas por par: Pearson dos ângulos, bruta e sem mercado.
Com deslocamento (A_t × B_t+k, |k| ≤ desvio_max_candles, só dentro do dia), melhor k por par:
  - correlação: andam juntos, sem olhar o tamanho;
  - razão: média por minuto de menor/maior (sinal oposto → negativo; os dois parados (ângulo 0) = 1; só um parado = 0).
    +10% × +10% = 100%; 1% × 1,1% = 90,9%. Estudo, nunca sinal.
"""

import numpy as np
import pandas as pd

from copiloto import mercado, negocios, similaridade
from copiloto.config import Config



def _vwap_ticks(cfg: Config, ticker: str, desde_ms: int) -> pd.Series:
    with negocios.conectar(cfg) as con:
        linhas = con.execute("SELECT t / 60000 AS m, SUM(ultimo * volume) / SUM(volume) FROM negocios "
                             "WHERE ticker = ? AND t >= ? AND volume > 0 GROUP BY m ORDER BY m", (ticker, desde_ms)).fetchall()
    return pd.Series([p for _, p in linhas], index=pd.to_datetime([m * 60_000 for m, _ in linhas], unit="ms"))


def _ohlc4(cfg: Config, ticker: str, sessoes: int) -> pd.Series:
    v = mercado.ler(cfg, ticker, sessoes)
    return pd.Series([(c["abertura"] + c["maxima"] + c["minima"] + c["fechamento"]) / 4 for c in v],
                     index=pd.to_datetime([c["data_hora"] for c in v]))


def precos(cfg: Config, sessoes: int, fonte: str) -> pd.DataFrame:
    if fonte == "ticks":
        inicio = mercado.ler(cfg, cfg.universo.watchlist[0], sessoes)[0]["data_hora"]
        series = {t: _vwap_ticks(cfg, t, negocios.ms(inicio)) for t in cfg.universo.watchlist}
    else:
        series = {t: _ohlc4(cfg, t, sessoes) for t in cfg.universo.watchlist}
    df = pd.DataFrame({t: s[~s.index.duplicated()] for t, s in series.items() if len(s)}).sort_index()
    return df.groupby(df.index.date).ffill()  # minuto sem negócio = preço parado (só dentro do dia)


def _deslocado(x: np.ndarray, dia: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Linhas (A_t, B_t+k) com t e t+k no mesmo dia."""
    if k >= 0:
        a, b, ok = x[:len(x) - k], x[k:], dia[:len(dia) - k] == dia[k:]
    else:
        a, b, ok = x[-k:], x[:k], dia[-k:] == dia[:k]
    return a[ok], b[ok]


def por_deslocamento(ang: pd.DataFrame, desvio_max: int) -> dict[str, np.ndarray]:
    """Melhor correlação e melhor razão por par entre os deslocamentos −N..+N; e o k de cada uma."""
    x, dia, k_n = ang.values, np.asarray(ang.index.date), ang.shape[1]
    corr, corr_k = np.full((k_n, k_n), -np.inf), np.zeros((k_n, k_n), int)
    razao, razao_k = np.full((k_n, k_n), -np.inf), np.zeros((k_n, k_n), int)
    for k in range(-desvio_max, desvio_max + 1):
        a, b = _deslocado(x, dia, k)
        za, zb = (a - a.mean(0)) / a.std(0), (b - b.mean(0)) / b.std(0)
        c = za.T @ zb / len(a)
        for i in range(k_n):
            for j in range(k_n):
                if i == j:
                    continue
                if c[i, j] > corr[i, j]:
                    corr[i, j], corr_k[i, j] = c[i, j], k
                ai, bj = a[:, i], b[:, j]
                maior = np.maximum(np.abs(ai), np.abs(bj))
                r = np.where(maior == 0, 1.0, np.sign(ai * bj) * np.minimum(np.abs(ai), np.abs(bj)) / np.where(maior == 0, 1, maior))
                if r.mean() > razao[i, j]:
                    razao[i, j], razao_k[i, j] = r.mean(), k
    np.fill_diagonal(corr, 1.0)
    np.fill_diagonal(razao, 1.0)
    return {"corr": corr, "corr_k": corr_k, "razao": razao, "razao_k": razao_k}


def calcular(cfg: Config, sessoes: int = 63, fonte: str = "ticks") -> dict:
    p = precos(cfg, sessoes, fonte)
    tickers = list(p.columns)
    ang = (similaridade._retornos(p) * 10_000).dropna()  # bps/min, sem o 1º minuto do dia
    ang_res = similaridade._residual(ang)
    mats = {"angulo_bruta": ang.corr().values, "angulo_residual": ang_res.corr().values}
    desl = por_deslocamento(ang, cfg.similaridade.desvio_max_candles)
    mats |= {"angulo_corr": desl["corr"], "angulo_razao": desl["razao"]}
    r = similaridade._r
    pares = [{"a": tickers[i], "b": tickers[j], **{k: r(v[i, j]) for k, v in mats.items()}}
             for i in range(len(tickers)) for j in range(i + 1, len(tickers))]
    return {
        "amostra": {"fonte": "VWAP de cada minuto (ticks)" if fonte == "ticks" else "(O+H+L+C)/4 do candle M1",
                    "inicio": str(ang.index[0]), "fim": str(ang.index[-1]), "sessoes": len(set(ang.index.date)),
                    "minutos": len(ang)},
        "tickers": tickers,
        "matrizes": {k: [[r(x) for x in linha] for linha in v] for k, v in mats.items()}
                    | {"angulo_corr_k": desl["corr_k"].tolist(), "angulo_razao_k": desl["razao_k"].tolist()},
        "pares": sorted(pares, key=lambda x: -abs(x["angulo_residual"] or 0)),
        "autocorrelacao_angulo_lag1": {t: r(ang[t].autocorr(1)) for t in tickers},
        "limites": "demo; passado ≠ previsão",
    }
