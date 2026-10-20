"""Mercado: 1ª carga = dias_iniciais; depois só candles novos; candle em formação fica de fora."""

from datetime import datetime

from copiloto import mercado
from copiloto.config import carregar_config


class ServicoFalso:
    def __init__(self):
        self.pedidos = []

    def simbolos(self):
        return [{"ticker": "RADL3", "ponto": 0.01}, {"ticker": "XXXX3", "existe": False}]

    def candles(self, ticker, desde, ate):
        self.pedidos.append(desde)
        return [{"horario": f"2026-10-20T11:0{m}:00.000", "abertura": 20.0, "maxima": 20.0, "minima": 20.0,
                 "fechamento": 20.0, "volume_ticks": 1, "volume_real": 100.0, "spread_pts": 1} for m in range(4)]


def test_incremental(tmp_path):
    cfg = carregar_config()
    cfg.mercado.pasta, cfg.universo.watchlist = str(tmp_path), ["RADL3", "XXXX3"]
    s = ServicoFalso()
    r = mercado.atualizar(s, cfg, datetime(2026, 10, 20, 11, 2, 30))  # 11:02 em formação
    assert r == {"RADL3": 2, "XXXX3": "símbolo inexistente"}
    assert s.pedidos[0] == datetime(2026, 7, 22, 11, 2, 30)  # 90 dias
    assert mercado.ler(cfg, "RADL3")[0]["spread_pct"] == 0.05  # 0,01 / 20
    assert mercado.atualizar(s, cfg, datetime(2026, 10, 20, 11, 9))["RADL3"] == 2  # só 11:02 e 11:03
    assert s.pedidos[-1] == datetime(2026, 10, 20, 11, 2)
    assert len(mercado.ler(cfg, "RADL3")) == 4
