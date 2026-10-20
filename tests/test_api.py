"""API com serviço falso: só GET, erro MT5 → reconecta 1x → 503."""

from fastapi.testclient import TestClient

from copiloto.api import criar_app
from copiloto.config import carregar_config
from copiloto.mt5_servico import ErroMT5


class ServicoFalso:
    def __init__(self):
        self.cfg = carregar_config()
        self.conexoes, self.falhas = 0, 0

    def conectar(self, tentativas=None):
        self.conexoes += 1

    def conta(self):
        if self.falhas:
            self.falhas -= 1
            raise ErroMT5("caiu")
        return {"saldo": 1.0, "patrimonio": 1.0, "margem": 0.0, "margem_livre": 1.0}

    def posicoes(self):
        return []

    def ordens(self):
        return []

    def deals(self, dias=None):
        return [{"dias": dias}]

    def simbolos(self, tickers=None):
        return [{"ticker": t, "existe": False} for t in tickers or ["ABEV3"]]

    def margem_prevista(self, *_):
        return None


def _cliente(s):
    return TestClient(criar_app(lambda: s))


def test_recursos_da_cli():
    s = ServicoFalso()
    with _cliente(s) as c:
        assert c.get("/conta").json()["saldo"] == 1.0
        assert c.get("/posicoes").json() == [] and c.get("/ordens").json() == []
        assert c.get("/historico", params={"dias": 7}).json() == [{"dias": 7}]
        assert [x["ticker"] for x in c.get("/simbolos", params={"tickers": "radl3, itub4"}).json()] == ["RADL3", "ITUB4"]
        assert c.get("/capacidade").json()["modo"] == "simulado"
        assert c.get("/atencoes").json()[0]["tipo"] == "simbolo_sem_cotacao"
        assert c.get("/config").json()["painel"]["refresh_s"] > 0
        assert isinstance(c.get("/registro").json(), list) and isinstance(c.get("/base").json(), list)
        assert "drawdown_max" in c.get("/resultado").json()["total"]
        assert c.get("/spread").json()[0]["status"] == "sem_cotacao"
    assert s.conexoes == 0  # conexão só quando precisa


def test_somente_leitura():
    with _cliente(ServicoFalso()) as c:
        assert all(m == {"GET"} or m == {"GET", "HEAD"} for r in c.app.routes
                   if (m := getattr(r, "methods", None)) and r.path not in ("/openapi.json", "/docs", "/redoc",
                                                                             "/docs/oauth2-redirect"))
        assert c.post("/conta").status_code == 405


def test_reconecta_e_depois_503_rapido():
    s = ServicoFalso()
    with _cliente(s) as c:
        s.falhas = 1
        assert c.get("/conta").status_code == 200 and s.conexoes == 1
        s.falhas = 2
        r = c.get("/conta")
        assert r.status_code == 503 and "MT5 indisponível" in r.json()["detail"]
        assert c.get("/conta").status_code == 503 and s.conexoes == 2  # dentro da espera: nem tenta
        assert c.get("/config").status_code == 200  # não depende do MT5
