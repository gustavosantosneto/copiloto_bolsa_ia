"""Base operacional: Δmargem → margem/lote e alavancagem; só deal ao vivo sozinho no ciclo."""

from copiloto.config import carregar_config
from copiloto.medicao import consolidar, divergentes, medicoes

CFG = carregar_config()


def _deal(ticker="RADL3", antes=263.94, depois=125.21, prev=138.39, fonte="coletor", n=1, hora="2026-10-19T16:39:09.048"):
    return {"data_hora": hora, "ticker": ticker, "qtd": 1300.0, "preco": 21.29, "fonte": fonte, "deals_no_ciclo": n,
            "margem_antes": antes, "margem_depois": depois, "margem_prevista_mt5": prev, "ambiente": "demo"}


def test_mede_deal_do_csv():  # RADL3 2026-10-19 (demo)
    m = medicoes(CFG, [_deal()])[0]
    assert (m["delta_margem"], m["margem_por_lote"]) == (138.73, 10.67)  # 138,73 / 13 lotes
    assert m["alavancagem_medida"] == 199.5 and m["divergencia_pct"] == 0.25


def test_ignora_importado_multiplo_e_sem_delta():
    assert medicoes(CFG, [_deal(fonte="mt5_historico"), _deal(n=2), _deal(antes=10.0, depois=10.0), _deal(antes=None)]) == []


def test_consolida_mediana_e_status():
    ds = [_deal(hora=f"2026-10-19T10:0{i}:00.000", depois=125.21 - i) for i in range(3)] + [_deal("ITUB4")]
    base = {b["ticker"]: b for b in consolidar(CFG, ds)}
    assert base["RADL3"]["n_medicoes"] == 3 and base["RADL3"]["status"] == "observado"
    assert base["RADL3"]["margem_por_lote"] == 10.75  # mediana: 139,73 / 13
    assert base["ITUB4"]["status"] == "pendente"  # < min_medicoes_margem_validada


def test_divergencia_acima_da_tolerancia():
    assert divergentes(CFG, [_deal()]) == []
    assert divergentes(CFG, [_deal(prev=100.0)])[0]["divergencia_pct"] == 38.73
