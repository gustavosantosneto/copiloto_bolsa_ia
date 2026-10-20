"""Registro CSV: 1 linha por deal, sem duplicar, snapshot só quando capturado ao vivo."""

import csv

import pytest

from copiloto.config import carregar_config
from copiloto.registro import COLUNAS, COLUNAS_SEM_MOTIVO, Registro, ler


def _deal(ticket=1, tipo="venda", entrada="entrada", lucro=0.0):
    return {"ticket": ticket, "ordem": 10, "posicao": 20, "ticker": "RADL3", "tipo": tipo, "entrada": entrada,
            "volume": 100.0, "preco": 21.18, "comissao": -1.0, "taxa": -0.5, "swap": 0.0, "lucro": lucro,
            "horario": f"2026-10-19T10:45:{ticket:02d}.000"}


def _snap(margem):
    return {"horario": "2026-10-19T10:45:00.000", "saldo": 1000.0, "patrimonio": 1000.0, "margem": margem,
            "margem_livre": 1000.0 - margem, "nivel_margem": 0.0}


def _linhas(caminho):
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


@pytest.fixture
def reg(tmp_path):
    return Registro(carregar_config(), 123, tmp_path / "h.csv")


def test_importa_sem_duplicar_e_ignora_saldo(reg):
    deals = [_deal(2), _deal(1), {**_deal(3), "tipo": "saldo"}]
    assert reg.importar(deals) == 2
    assert reg.importar(deals) == 0
    linhas = _linhas(reg.caminho)
    assert [l["ticket_deal"] for l in linhas] == ["1", "2"]  # ordenado por horário
    assert linhas[0]["fonte"] == "mt5_historico" and linhas[0]["margem_antes"] == ""


def test_evento_grava_snapshot_e_custos(reg):
    ev = {"evento": "deal", "deal": _deal(5, lucro=30.0), "deals_no_ciclo": 1,
          "snapshot_antes": _snap(0.0), "snapshot_depois": _snap(10.7), "margem_prevista_mt5": 10.69}
    assert reg.gravar_evento(ev) == 1
    l = _linhas(reg.caminho)[0]
    assert (l["margem_antes"], l["margem_depois"], l["margem_prevista_mt5"]) == ("0.0", "10.7", "10.69")
    assert (l["custos"], l["resultado_liquido"], l["fonte"]) == ("-1.5", "28.5", "coletor")
    assert reg.gravar_evento(ev) == 0  # mesmo ticket


def test_reabre_arquivo_e_lembra_tickets(tmp_path):
    cfg = carregar_config()
    Registro(cfg, 1, tmp_path / "h.csv").importar([_deal(1)])
    assert Registro(cfg, 1, tmp_path / "h.csv").importar([_deal(1)]) == 0


def test_cabecalho_diferente_recusa(tmp_path):
    (tmp_path / "h.csv").write_text("a;b\n1;2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="cabeçalho"):
        Registro(carregar_config(), 1, tmp_path / "h.csv")


def test_colunas_cobrem_regra_de_gestao():
    for k in ("saldo", "patrimonio", "margem", "margem_livre", "nivel_margem"):
        assert f"{k}_antes" in COLUNAS and f"{k}_depois" in COLUNAS


def test_ler_converte_e_filtra_por_dia(reg):
    from datetime import date
    hoje = date.today().isoformat()
    reg.importar([{**_deal(1), "horario": "2020-01-01T10:00:00.000"}, {**_deal(2), "horario": f"{hoje}T10:00:00.000"}])
    r = ler(carregar_config(), 1, reg.caminho)
    assert [x["ticket_deal"] for x in r] == [2]
    assert r[0]["preco"] == 21.18 and r[0]["margem_antes"] is None and r[0]["ticker"] == "RADL3"


def test_migra_csv_sem_motivo_e_completa_pelo_mt5(tmp_path):
    caminho = tmp_path / "h.csv"
    linha = {k: "" for k in COLUNAS_SEM_MOTIVO} | {"ticket_deal": "1", "data_hora": "2026-10-19T10:00:00.000"}
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLUNAS_SEM_MOTIVO, delimiter=";")
        w.writeheader()
        w.writerow(linha)
    reg = Registro(carregar_config(), 1, caminho)
    assert _linhas(caminho)[0]["motivo"] == ""
    reg.importar([{**_deal(1), "motivo": "tp"}])
    assert _linhas(caminho)[0]["motivo"] == "tp" and len(_linhas(caminho)) == 1
