"""Similaridade: overnight fora do retorno; residual tira o mercado; atraso conhecido é achado; BH monotônico."""

import numpy as np
import pandas as pd

from copiloto import similaridade as s


def test_retorno_descarta_overnight():
    idx = pd.to_datetime(["2026-10-19 16:58", "2026-10-19 16:59", "2026-10-20 10:00", "2026-10-20 10:01"])
    r = s._retornos(pd.DataFrame({"A": [10.0, 10.1, 12.0, 12.1]}, index=idx))
    assert list(r.index) == [idx[1], idx[3]]  # 10:00 (gap da noite) some


def test_residual_remove_fator_comum():
    rng = np.random.default_rng(1)
    mercado = rng.normal(0, 1, 2000)
    df = pd.DataFrame({c: mercado + rng.normal(0, 0.3, 2000) for c in "ABCD"})
    assert df.corr().values[0, 1] > 0.8
    assert abs(s._residual(df).corr().values[0, 1]) < 0.4


def test_atraso_conhecido():
    rng = np.random.default_rng(2)
    n = 3000
    a = rng.normal(0, 1, n)
    b = np.roll(a, 3) * 0.6 + rng.normal(0, 1, n)  # B segue A com 3 candles
    idx = pd.date_range("2026-10-20 10:00", periods=n, freq="1min")
    pares = {(p["lider"], p["seguidor"]): p for p in s._atrasos(pd.DataFrame({"A": a, "B": b}, index=idx), 5)}
    assert pares[("A", "B")]["lag"] == 3 and pares[("A", "B")]["q"] < 0.01
    assert pares[("B", "A")]["q"] > 0.01


def test_bh():
    q = s._bh([0.01, 0.04, 0.03, 0.5])
    assert [round(x, 3) for x in q] == [0.04, 0.053, 0.053, 0.5]
