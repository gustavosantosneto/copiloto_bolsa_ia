"""Guardas: cotação parada no pregão, posição fantasma, margem zero."""

from datetime import datetime

from copiloto.config import carregar_config
from copiloto.guardas import cotacao_viva, verificar

CFG = carregar_config()
PREGAO, NOITE = datetime(2026, 10, 19, 11, 0, 30), datetime(2026, 10, 19, 20, 0)
VIVA = {"ticker": "RADL3", "existe": True, "ask": 21.4, "ultimo": 21.4, "horario_cotacao": "2026-10-19T11:00:00.000"}
PARADA = {"ticker": "WDOG26", "existe": True, "ask": 5230.0, "ultimo": 5230.0, "horario_cotacao": "2026-01-30T17:00:00.000"}
FANTASMA = {"ticker": "WDOG26", "volume": 1.0, "lucro": 50.0}


def test_cotacao_viva_por_idade_so_no_pregao():
    assert cotacao_viva(CFG, VIVA, PREGAO)
    assert not cotacao_viva(CFG, PARADA, PREGAO)
    assert cotacao_viva(CFG, PARADA, NOITE)  # fora do pregão não exige tick novo
    assert not cotacao_viva(CFG, {"ticker": "X", "existe": False}, NOITE)


def test_posicao_fantasma_gera_dois_alertas():
    a = verificar(CFG, {"margem": 0.0}, [FANTASMA], [VIVA, PARADA], PREGAO)
    assert [(x["tipo"], x.get("ticker")) for x in a] == [("simbolo_sem_cotacao", "WDOG26"), ("margem_zero_com_posicao", None)]
    assert a[0]["em_carteira"] and a[1]["tickers"] == ["WDOG26"]


def test_tudo_normal_sem_alertas():
    assert verificar(CFG, {"margem": 10.0}, [{**FANTASMA, "ticker": "RADL3"}], [VIVA], PREGAO) == []


def test_posicao_em_simbolo_nao_consultado():
    a = verificar(CFG, {"margem": 10.0}, [FANTASMA], [VIVA], PREGAO)
    assert a[0]["ticker"] == "WDOG26" and a[0]["em_carteira"]
