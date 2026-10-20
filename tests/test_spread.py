"""Spread: % do meio; teto > média + N ticks; referência só com amostra mínima; atenção só no pregão."""

from datetime import datetime

import pytest

from copiloto import spread
from copiloto.config import carregar_config

PREGAO, NOITE = datetime(2026, 10, 20, 11, 0), datetime(2026, 10, 20, 20, 0)


@pytest.fixture
def cfg(tmp_path):
    c = carregar_config()
    c.mercado.pasta = str(tmp_path)
    c.spread.min_amostras = 3
    spread._cache.clear()
    return c


def _m1(cfg, ticker, valores):
    linhas = ["data_hora;abertura;maxima;minima;fechamento;volume_ticks;volume_real;spread_pts;spread_pct"]
    linhas += [f"2026-10-19T10:{i:02d}:00.000;20;20;20;20;1;100;{v};{v * 0.05}" for i, v in enumerate(valores)]
    (spread.mercado.arquivo(cfg, ticker)).write_text("\n".join(linhas) + "\n", encoding="utf-8")


def _s(bid, ask, t="RADL3"):
    return {"ticker": t, "bid": bid, "ask": ask, "ponto": 0.01}


def test_spread_pct_do_meio():
    assert round(spread.spread_pct(_s(19.99, 20.01)), 4) == 0.1
    assert spread.spread_pct(_s(None, 20.0)) is None and spread.spread_pct(_s(20.1, 20.0)) is None


def test_status(cfg):
    _m1(cfg, "RADL3", [1, 1, 1, 1])  # média 1 tick
    st = lambda b, a: spread.avaliar(cfg, [_s(b, a)])[0]["status"]  # noqa: E731
    assert st(20.0, 20.03) == "ok"  # 3 ticks = média + 2 (não passa)
    assert st(20.0, 20.04) == "anormal"  # 4 ticks > média + 2
    assert st(20.0, 20.2) == "teto"  # ~1% > 0,5%
    assert spread.avaliar(cfg, [_s(20.0, 20.01, "ITUB4")])[0]["status"] == "sem_referencia"
    assert spread.avaliar(cfg, [_s(None, None)])[0]["status"] == "sem_cotacao"


def test_atencao_so_no_pregao(cfg):
    _m1(cfg, "RADL3", [1, 1, 1, 1])
    av = spread.avaliar(cfg, [_s(20.0, 20.2)])
    assert [a["tipo"] for a in spread.atencoes(cfg, av, PREGAO)] == ["spread_teto"]
    assert spread.atencoes(cfg, av, NOITE) == []
