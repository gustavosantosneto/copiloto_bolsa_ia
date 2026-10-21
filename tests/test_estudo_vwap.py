"""Ângulo com deslocamento: razão menor/maior (parado × parado = 1, um parado = 0) e melhor k."""

import pandas as pd

from copiloto import estudo_vwap as e


def _df(a, b):
    return pd.DataFrame({"A": a, "B": b}, index=pd.date_range("2026-10-20 10:00", periods=len(a), freq="1min"))


def test_razao_sem_deslocamento():
    d = e.por_deslocamento(_df([1.0, 0, -2, 10, 0, 1], [1.1, 0, -2, 10, 3, 1]), 0)
    assert round(d["razao"][0, 1], 4) == round((1 / 1.1 + 1 + 1 + 1 + 0 + 1) / 6, 4)


def test_b_segue_a_dois_minutos_depois():
    d = e.por_deslocamento(_df([0, 5, 0, 0, -3, 0, 0, 0], [0, 0, 0, 5, 0, 0, -3, 0]), 3)
    assert (d["corr_k"][0, 1], d["razao_k"][0, 1], d["razao"][0, 1]) == (2, 2, 1.0)
