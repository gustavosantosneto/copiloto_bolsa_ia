"""API somente leitura (GET) — mesmos recursos da CLI. Painel web consome daqui."""

import threading
import time
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from copiloto import corretoras, diagnostico, medicao, registro, resultado, similaridade, spread
from copiloto.capacidade import calcular
from copiloto.config import carregar_config
from copiloto.guardas import atencoes_atuais
from copiloto.mt5_servico import ErroMT5, ServicoMT5


def criar_app(fabrica: Callable[[], ServicoMT5] = lambda: ServicoMT5(carregar_config())) -> FastAPI:
    estado: dict = {"falha": None}  # falha = (horário, msg) da última conexão falha
    trava = threading.Lock()  # SDK MT5 é global ao processo → 1 chamada por vez
    ESPERA_S = 5  # após falha, responde 503 direto por X s (não trava o painel)

    @asynccontextmanager
    async def ciclo_de_vida(_app):
        estado["s"] = fabrica()  # conexão só na 1ª requisição → API sobe na hora
        yield

    app = FastAPI(title="copiloto_bolsa_ia", description="Somente leitura. Nenhuma ordem é enviada.",
                  lifespan=ciclo_de_vida)

    def _ler(funcao: Callable[[ServicoMT5], object]):
        s = estado["s"]
        with trava:
            if estado["falha"] and time.monotonic() - estado["falha"][0] < ESPERA_S:
                raise HTTPException(503, estado["falha"][1])
            try:
                return funcao(s)
            except ErroMT5:
                try:  # sem conexão → 1 tentativa e repete
                    s.conectar(tentativas=0)
                    estado["falha"] = None
                    return funcao(s)
                except ErroMT5 as e:
                    estado["falha"] = (time.monotonic(), f"MT5 indisponível: {e}")
                    raise HTTPException(503, estado["falha"][1]) from e

    @app.get("/conta")
    def conta():
        return _ler(lambda s: s.conta())

    @app.get("/posicoes")
    def posicoes():
        return _ler(lambda s: s.posicoes())

    @app.get("/ordens")
    def ordens():
        return _ler(lambda s: s.ordens())

    @app.get("/historico")
    def historico(dias: int | None = None):
        return _ler(lambda s: s.deals(dias=dias))

    @app.get("/simbolos")
    def simbolos(tickers: str | None = None):
        lista = [t.strip().upper() for t in tickers.split(",")] if tickers else None
        return _ler(lambda s: s.simbolos(lista))

    @app.get("/capacidade")
    def capacidade():
        return _ler(lambda s: calcular(s.cfg, s.conta(), s.posicoes(), s.simbolos(),
                                       lambda t, v, p: s.margem_prevista(t, "compra", v, p)))

    @app.get("/registro")
    def registro_deals(dias: int = 1):
        return registro.ler(estado["s"].cfg, dias)

    @app.get("/base")
    def base():
        cfg = estado["s"].cfg
        return medicao.consolidar(cfg, registro.ler(cfg, None))

    @app.get("/resultado")
    def resultado_realizado(dias: int = 30):
        cfg = estado["s"].cfg
        return resultado.calcular(cfg, registro.ler(cfg, dias))

    @app.get("/corretoras")
    def corretoras_simulacao():
        return _ler(lambda s: corretoras.simular(s.cfg, s.conta(), s.posicoes(), s.simbolos()))

    @app.get("/diagnostico")
    def diagnostico_operacoes(dias: int = 30):
        cfg = estado["s"].cfg
        return diagnostico.calcular(cfg, registro.ler(cfg, dias))

    @app.get("/similaridade")
    def similaridade_ao_vivo():
        return _ler(lambda s: similaridade.ao_vivo(s, s.cfg))  # últimos janela_minutos, direto do MT5

    @app.get("/spread")
    def spread_atual():
        return _ler(lambda s: spread.avaliar(s.cfg, s.simbolos()))

    @app.get("/config")
    def config():
        return estado["s"].cfg.model_dump(mode="json")  # senha mascarada

    @app.get("/atencoes")
    def atencoes():
        return _ler(atencoes_atuais)

    return app
