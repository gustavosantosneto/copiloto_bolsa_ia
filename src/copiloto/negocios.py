"""Negócios tick a tick p/ estudo → SQLite ([mercado].banco_ticks). Incremental por ticker (após o último gravado).

Dado de mercado = estudo/fixture, nunca sinal. t = epoch ms no horário do servidor (como o MT5 devolve).
flags: 32 = agressão compra, 64 = agressão venda. bid/ask = livro no momento do negócio.
"""

import sqlite3
from datetime import UTC, datetime, timedelta

from copiloto.config import RAIZ, Config

AGRESSAO_COMPRA, AGRESSAO_VENDA = 32, 64


def conectar(cfg: Config) -> sqlite3.Connection:
    caminho = RAIZ / cfg.mercado.banco_ticks
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(caminho)
    con.execute("CREATE TABLE IF NOT EXISTS negocios (ticker TEXT NOT NULL, t INTEGER NOT NULL, bid REAL, ask REAL, "
                "ultimo REAL, volume REAL, flags INTEGER)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_negocios ON negocios (ticker, t)")
    return con


def ms(horario: str) -> int:
    """ISO do servidor (sem fuso) → epoch ms no mesmo referencial dos ticks."""
    return int(datetime.fromisoformat(horario).replace(tzinfo=UTC).timestamp() * 1000)


def atualizar(servico, cfg: Config, agora: datetime | None = None) -> dict[str, int | str]:
    """Watchlist: 1ª vez = dias_iniciais; depois só depois do último negócio gravado."""
    agora, saida = agora or datetime.now(), {}
    existe = {s["ticker"]: s.get("existe", True) for s in servico.simbolos()}
    with conectar(cfg) as con:
        for t in cfg.universo.watchlist:
            if not existe.get(t):
                saida[t] = "símbolo inexistente"
                continue
            (ultimo,) = con.execute("SELECT MAX(t) FROM negocios WHERE ticker = ?", (t,)).fetchone()
            desde = (datetime.fromtimestamp((ultimo + 1) / 1000, UTC).replace(tzinfo=None) if ultimo
                     else agora - timedelta(days=cfg.mercado.dias_iniciais))
            n = 0
            for bloco in servico.negocios(t, desde, agora):
                novos = [(t, *x) for x in bloco if not ultimo or x[0] > ultimo]
                con.executemany("INSERT INTO negocios VALUES (?, ?, ?, ?, ?, ?, ?)", novos)
                n += len(novos)
            saida[t] = n
    return saida


def ler(con: sqlite3.Connection, ticker: str, de_ms: int, ate_ms: int) -> list[tuple]:
    """(t, bid, ask, ultimo, volume, flags) em ordem de tempo."""
    return con.execute("SELECT t, bid, ask, ultimo, volume, flags FROM negocios WHERE ticker = ? AND t BETWEEN ? AND ? "
                       "ORDER BY t", (ticker, de_ms, ate_ms)).fetchall()
