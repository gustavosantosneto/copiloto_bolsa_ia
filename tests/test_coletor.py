"""Coletor com serviço falso: diff de deals/posições/ordens e snapshots."""

from copiloto.coletor import Coletor
from copiloto.config import carregar_config
from copiloto.mt5_servico import ErroMT5


def _conta(margem: float) -> dict:
    return {"saldo": 1000.0, "patrimonio": 1000.0, "margem": margem, "margem_livre": 1000.0 - margem, "nivel_margem": 0.0}


def _pos(ticket=10, volume=100.0, tp=0.0) -> dict:
    return {"ticket": ticket, "ticker": "ABEV3", "volume": volume, "preco_medio": 16.5, "sl": 0.0, "tp": tp}


class ServicoFalso:
    """Estado mutável; `margens` = fila de leituras de conta."""

    def __init__(self):
        self.margens = [0.0]
        self.lista_deals, self.lista_posicoes, self.lista_ordens = [], [], []
        self.falhar = False
        self.reconexoes = 0

    def conta(self):
        if self.falhar:
            raise ErroMT5("caiu")
        return _conta(self.margens.pop(0) if len(self.margens) > 1 else self.margens[0])

    def deals(self, dias=None):
        return list(self.lista_deals)

    def posicoes(self):
        return list(self.lista_posicoes)

    def ordens(self):
        return list(self.lista_ordens)

    def margem_prevista(self, ticker, tipo, volume, preco):
        return 10.0

    def conectar(self):
        self.reconexoes += 1


def _coletor():
    s = ServicoFalso()
    return s, Coletor(s, carregar_config())


def test_primeiro_ciclo_e_linha_de_base():
    s, c = _coletor()
    s.lista_deals = [{"ticket": 1}]
    s.lista_posicoes = [_pos()]
    assert c.ciclo() == []


def test_deal_novo_com_snapshot_antes_e_depois():
    s, c = _coletor()
    c.ciclo()  # base: margem 0
    s.margens = [0.0, 50.0]  # leitura do ciclo (ainda 0) e releitura pós-deal (50)
    s.lista_deals = [{"ticket": 7, "ticker": "ABEV3", "tipo": "compra", "volume": 100.0, "preco": 16.5}]
    s.lista_posicoes = [_pos()]
    ev = c.ciclo()
    deal = next(e for e in ev if e["evento"] == "deal")
    assert deal["deal"]["ticket"] == 7
    assert deal["snapshot_antes"]["margem"] == 0.0
    assert deal["snapshot_depois"]["margem"] == 50.0
    assert deal["margem_prevista_mt5"] == 10.0
    assert {e["evento"] for e in ev} == {"deal", "posicao_aberta"}
    assert c.ciclo() == []  # mesmo deal não repete


def test_posicao_alterada_e_encerrada():
    s, c = _coletor()
    s.lista_posicoes = [_pos()]
    c.ciclo()
    s.lista_posicoes = [_pos(volume=200.0, tp=17.0)]
    ev = c.ciclo()
    assert ev[0]["evento"] == "posicao_alterada"
    assert ev[0]["mudancas"] == {"volume": [100.0, 200.0], "tp": [0.0, 17.0]}
    s.lista_posicoes = []
    assert c.ciclo()[0]["evento"] == "posicao_encerrada"


def test_ordem_nova():
    s, c = _coletor()
    c.ciclo()
    s.lista_ordens = [{"ticket": 3, "volume_atual": 100.0, "preco": 16.0, "sl": 0.0, "tp": 0.0}]
    assert c.ciclo()[0]["evento"] == "ordem_aberta"


def test_erro_mt5_reconecta_e_segue():
    s, c = _coletor()
    s.falhar = True
    ev = list(c.rodar(ciclos=2, dormir=lambda _: None))
    assert [e["evento"] for e in ev] == ["erro_mt5", "erro_mt5"]
    assert s.reconexoes == 2
    s.falhar = False
    assert list(c.rodar(ciclos=1, dormir=lambda _: None)) == []


def test_intervalo_usa_config():
    _, c = _coletor()
    assert c.intervalo() in (c.cfg.coletor.intervalo_poll_s, c.cfg.coletor.intervalo_poll_fora_pregao_s)

