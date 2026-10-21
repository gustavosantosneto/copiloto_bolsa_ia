"""Similaridade entre ativos (V2): correlação direta/inversa, atraso líder→seguidor, cointegração, Granger.

Base = retornos log intradiários (retorno entre pregões descartado), nunca preço — exceto cointegração (log-preço).
Bruta e residual (sem mercado: desconta beta × média dos OUTROS ativos da watchlist).
Base = últimos janela_sessoes (~90 dias); estabilidade semanal (fração de semanas com o mesmo sinal).
Muitos testes ao mesmo tempo → q-valor Benjamini-Hochberg (fdr_max).
ao_vivo(): matriz do painel = últimos janela_minutos, ângulo da VWAP de cada minuto (ticks direto do MT5).
Correlação ≠ causalidade; Granger = antecipação estatística, não causa. Estudo, nunca sinal.
"""

import json
import math
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint, grangercausalitytests

from copiloto import mercado
from copiloto.config import RAIZ, Config

MAX_GRANGER = 40  # Granger é caro → só nos pares com atraso mais forte


def _minutos(tf: str) -> int:
    return {"M": 1, "H": 60}[tf[0]] * int(tf[1:])


def _precos(cfg: Config) -> pd.DataFrame:
    """Fechamento M1 por ticker (colunas), forward-fill só dentro do dia (minuto sem negócio = preço parado)."""
    series = {}
    for t in cfg.universo.watchlist:
        velas = mercado.ler(cfg, t)
        if velas:
            s = pd.Series([v["fechamento"] for v in velas], index=pd.to_datetime([v["data_hora"] for v in velas]))
            series[t] = s[~s.index.duplicated()]
    df = pd.DataFrame(series).sort_index()
    return df.groupby(df.index.date).ffill()


def _reamostrar(precos: pd.DataFrame, tf: str) -> pd.DataFrame:
    n = _minutos(tf)
    return precos if n == 1 else precos.resample(f"{n}min").last().dropna(how="all")


def _retornos(precos: pd.DataFrame) -> pd.DataFrame:
    r = np.log(precos).diff()
    dia = pd.Series(precos.index.date, index=precos.index)
    r[dia != dia.shift()] = np.nan  # 1º candle do dia: retorno do overnight fica fora
    return r.dropna()


def _janela(df: pd.DataFrame, sessoes: int) -> pd.DataFrame:
    dias = sorted(set(df.index.date))[-sessoes:]
    return df[df.index.date >= dias[0]] if dias else df


def _residual(r: pd.DataFrame) -> pd.DataFrame:
    saida = {}
    for c in r.columns:
        m = r.drop(columns=c).mean(axis=1)
        beta = r[c].cov(m) / m.var()
        saida[c] = r[c] - beta * m
    return pd.DataFrame(saida)


def _estabilidade(r: pd.DataFrame) -> np.ndarray:
    """Fração das semanas em que a correlação tem o mesmo sinal da janela toda."""
    total = np.sign(r.corr().values)
    semanas = [g.corr().values for _, g in r.groupby(r.index.to_period("W")) if len(g) > 20]
    if not semanas:
        return np.full_like(total, np.nan)
    return np.mean([np.sign(s) == total for s in semanas], axis=0)


def _bh(p: list[float]) -> list[float]:
    """q-valores Benjamini-Hochberg."""
    n = len(p)
    if not n:
        return []
    ordem = np.argsort(p)
    q = np.empty(n)
    menor = 1.0
    for pos in range(n - 1, -1, -1):
        i = ordem[pos]
        menor = min(menor, p[i] * n / (pos + 1))
        q[i] = menor
    return q.tolist()


def _atrasos(r: pd.DataFrame, lag_max: int) -> list[dict]:
    """corr(A_t, B_t+L), L = 1..lag_max, só dentro do mesmo dia. Melhor L por par; p ajustado pelos L testados."""
    x, dia, cols = r.values, r.index.date, list(r.columns)
    melhor: dict[tuple[int, int], tuple[float, int, int]] = {}
    for lag in range(1, lag_max + 1):
        ok = dia[:-lag] == dia[lag:]
        a, b = x[:-lag][ok], x[lag:][ok]
        a = (a - a.mean(0)) / a.std(0)
        b = (b - b.mean(0)) / b.std(0)
        c = a.T @ b / len(a)  # c[i, j] = i antecipa j em `lag` candles
        for i in range(len(cols)):
            for j in range(len(cols)):
                if i != j and abs(c[i, j]) > abs(melhor.get((i, j), (0.0, 0, 0))[0]):
                    melhor[(i, j)] = (float(c[i, j]), lag, len(a))
    pares = []
    for (i, j), (rho, lag, n) in melhor.items():
        p = min(1.0, math.erfc(abs(rho) * math.sqrt(n) / math.sqrt(2)) * lag_max)
        pares.append({"lider": cols[i], "seguidor": cols[j], "lag": lag, "rho": rho, "p": p, "n": n})
    for par, q in zip(pares, _bh([x["p"] for x in pares])):
        par["q"] = q
    return pares


def _granger(r: pd.DataFrame, par: dict, lag_max: int) -> float:
    """p mínimo (teste F) de 'líder Granger-antecipa seguidor', ajustado pelos lags testados."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = grangercausalitytests(r[[par["seguidor"], par["lider"]]].values, maxlag=lag_max)
    return min(1.0, min(v[0]["ssr_ftest"][1] for v in res.values()) * lag_max)


def _r(v, c=3):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else round(float(v), c)


def calcular(cfg: Config) -> dict:
    s = cfg.similaridade
    m1 = _precos(cfg)
    precos = _janela(_reamostrar(m1, s.timeframe), s.janela_sessoes).dropna(axis=1, thresh=100)
    tickers = list(precos.columns)
    r = _retornos(precos)
    bases = {"bruta": r, "residual": _residual(r)}
    matrizes = {nome: df.corr().values for nome, df in bases.items()}
    estab = _estabilidade(bases["residual"])

    # cointegração: log-preço (níveis), todos os pares
    lp = np.log(precos.ffill().dropna())
    cpares = [(i, j) for i in range(len(tickers)) for j in range(i + 1, len(tickers))]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cp = [coint(lp.iloc[:, i], lp.iloc[:, j])[1] for i, j in cpares]
    cq = dict(zip(cpares, _bh(cp)))

    pares = []
    for i, j in cpares:
        rb, rr = matrizes["bruta"][i, j], matrizes["residual"][i, j]
        tipo = "direta" if rb >= s.limiar_direta else "inversa" if rb <= s.limiar_inversa else None
        pares.append({"a": tickers[i], "b": tickers[j], "bruta": _r(rb), "residual": _r(rr),
                      "estabilidade": _r(estab[i, j], 2), "coint_q": _r(cq[(i, j)], 4), "tipo": tipo})
    pares.sort(key=lambda p: -abs(p["residual"] or 0))

    # atraso em M1 (residual), Granger só nos mais fortes significativos
    r1 = _residual(_retornos(_janela(m1[tickers], s.janela_sessoes).dropna()))
    atrasos = [a for a in _atrasos(r1, s.lag_max_candles) if a["q"] <= s.fdr_max]
    atrasos.sort(key=lambda a: -abs(a["rho"]))
    gp = [_granger(r1, a, s.lag_max_candles) for a in atrasos[:MAX_GRANGER]]
    for a, q in zip(atrasos, _bh(gp)):
        a["granger_q"] = q

    return {
        "calculado_em": datetime.now().isoformat(timespec="seconds"),
        "amostra": {"timeframe": s.timeframe, "timeframe_atraso": s.timeframe_atraso, "inicio": str(r.index[0]),
                    "fim": str(r.index[-1]), "sessoes": len(set(r.index.date)), "candles": len(r),
                    "candles_atraso": len(r1)},
        "tickers": tickers,
        "matrizes": {k: [[_r(v) for v in linha] for linha in m] for k, m in matrizes.items()}
                    | {"estabilidade": [[_r(v, 2) for v in linha] for linha in estab]},
        "pares": pares,
        "atrasos": [{"lider": a["lider"], "seguidor": a["seguidor"], "lag_min": a["lag"] * _minutos(s.timeframe_atraso),
                     "rho": _r(a["rho"]), "q": _r(a["q"], 4), "granger_q": _r(a.get("granger_q"), 4)} for a in atrasos],
        "limites": "demo; ~90 dias; retornos log intradiários; correlação ≠ causalidade; Granger = antecipação estatística; "
                   "passado ≠ previsão; validar fora da amostra antes de usar",
    }


def gravar(cfg: Config) -> Path:
    d = calcular(cfg)
    destino = RAIZ / cfg.similaridade.arquivo
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return destino


def ler(cfg: Config) -> dict | None:
    caminho = RAIZ / cfg.similaridade.arquivo
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else None


def ao_vivo(servico, cfg: Config, agora: datetime | None = None) -> dict:
    """Matriz dos últimos janela_minutos da sessão atual (ou da última, fora do pregão), direto do MT5.

    Preço de cada minuto = VWAP dos negócios do minuto; ângulo = ln(P_t / P_t−1) em bps. Medidas por par:
    bruta e sem mercado (mesmo minuto); correlação e razão com deslocamento ±desvio_max_candles (melhor k).
    """
    from copiloto import estudo_vwap  # estudo_vwap importa este módulo

    s, agora = cfg.similaridade, agora or datetime.now()
    precos = {}
    for t in cfg.universo.watchlist:
        neg = [x for bloco in servico.negocios(t, agora - pd.Timedelta(days=4), agora) for x in bloco if x[4] > 0]
        if neg:
            df = pd.DataFrame(neg, columns=["t", "bid", "ask", "ultimo", "volume", "flags"])
            df["min"] = pd.to_datetime(df["t"] // 60_000 * 60_000, unit="ms")
            g = df.assign(pv=df["ultimo"] * df["volume"]).groupby("min")
            precos[t] = g["pv"].sum() / g["volume"].sum()
    p = pd.DataFrame(precos).sort_index()
    p = p.between_time(cfg.pregao.abertura, cfg.pregao.fechamento)  # fora do pregão (leilão/after) não conta
    p = p[p.index.date == p.index[-1].date()]  # só a última sessão
    p = p[p.index > p.index[-1] - pd.Timedelta(minutes=s.janela_minutos)]
    p = p.reindex(pd.date_range(p.index[0], p.index[-1], freq="1min")).ffill()  # minuto sem negócio = parado
    ang = (_retornos(p) * 10_000).dropna(axis=1, how="any")
    tickers = list(ang.columns)
    desl = estudo_vwap.por_deslocamento(ang, s.desvio_max_candles)
    mats = {"bruta": ang.corr().values, "residual": _residual(ang).corr().values,
            "angulo_corr": desl["corr"], "angulo_razao": desl["razao"]}
    return {
        "calculado_em": agora.isoformat(timespec="seconds"),
        "amostra": {"inicio": str(ang.index[0]), "fim": str(ang.index[-1]), "minutos": len(ang),
                    "desvio_max_candles": s.desvio_max_candles, "fonte": "VWAP de cada minuto (ticks)"},
        "tickers": tickers,
        "matrizes": {k: [[_r(v) for v in linha] for linha in m] for k, m in mats.items()}
                    | {"angulo_corr_k": desl["corr_k"].tolist(), "angulo_razao_k": desl["razao_k"].tolist()},
        "limites": f"{len(ang)} minutos = poucos pontos: |ρ| < ~{2 / math.sqrt(max(len(ang), 4)):.2f} pode ser acaso "
                   f"(±k: melhor de {2 * s.desvio_max_candles + 1} deslocamentos, tende a sair maior); estudo, nunca sinal",
    }
