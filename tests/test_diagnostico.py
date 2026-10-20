"""Diagnóstico: P&L aberto tick a tick com entradas/saídas parciais → MAE/MFE; operação sem ticks marcada."""

import pytest

from copiloto import diagnostico, negocios
from copiloto.config import carregar_config


def _d(hora, tipo, entrada, qtd, preco, pos=1, bruto=0.0, motivo="manual"):
    return {"data_hora": f"2026-10-20T{hora}.000", "ticker": "RADL3", "tipo": tipo, "entrada": entrada, "qtd": qtd,
            "preco": preco, "ticket_posicao": pos, "resultado_bruto": bruto, "motivo": motivo}


def _t(hora, preco):
    return (negocios.ms(f"2026-10-20T{hora}.000"), preco, preco, preco, 100.0, 32)


OP = [_d("10:00:00", "venda", "entrada", 100, 20.0), _d("10:10:00", "venda", "entrada", 100, 20.2),
      _d("10:30:00", "compra", "saida", 200, 19.9, bruto=40.0, motivo="tp")]


def test_venda_com_preco_medio():
    ticks = [_t("10:00:00", 20.0), _t("10:05:00", 20.1), _t("10:10:00", 20.2), _t("10:20:00", 20.4), _t("10:30:00", 19.9)]
    e = diagnostico.excursao(OP, ticks)
    assert (e["qtd_max"], round(e["pm"], 2)) == (200, 20.1)
    assert round(e["mae"], 2) == -60.0  # (20,1 − 20,4) × 200
    assert e["min_ate_mae"] == 20.0 and e["mfe"] == 0  # saída no tick 19,9 zera o volume antes do P&L


def test_agrupa_so_encerradas_e_completas():
    aberta = [_d("11:00:00", "compra", "entrada", 100, 20.0, pos=2)]
    orfa = [_d("11:00:00", "compra", "saida", 100, 20.0, pos=3)]
    assert [ops[0]["ticket_posicao"] for ops in diagnostico.operacoes(OP + aberta + orfa)] == [1]


@pytest.fixture
def cfg(tmp_path):
    c = carregar_config()
    c.mercado.banco_ticks = str(tmp_path / "t.sqlite")
    return c


def test_calcular_marca_sem_ticks(cfg):
    r = diagnostico.calcular(cfg, OP)
    assert r["operacoes"][0]["status"] == "sem_ticks" and r["resumo"]["sem_ticks"] == 1
    with negocios.conectar(cfg) as con:
        con.executemany("INSERT INTO negocios VALUES ('RADL3', ?, ?, ?, ?, ?, ?)", [_t("10:01:00", 20.3)])
    assert diagnostico.calcular(cfg, OP)["operacoes"][0]["status"] == "sem_ticks"  # não cobre o fim (10:30)
    with negocios.conectar(cfg) as con:
        con.executemany("INSERT INTO negocios VALUES ('RADL3', ?, ?, ?, ?, ?, ?)", [_t("10:29:00", 19.95)])
    o = diagnostico.calcular(cfg, OP)["operacoes"][0]
    assert o["status"] == "ok" and (o["mae"], o["mfe"]) == (-30.0, 30.0) and o["motivo_saida"] == "tp"
