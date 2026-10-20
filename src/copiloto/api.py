"""API somente leitura (GET) — mesmos recursos da CLI. Painel web consome daqui."""

import threading
import time
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from copiloto import registro
from copiloto.capacidade import calcular
from copiloto.config import carregar_config
from copiloto.guardas import alertas_atuais
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

    @app.get("/config")
    def config():
        return estado["s"].cfg.model_dump(mode="json")  # senha mascarada

    @app.get("/alertas")
    def alertas():
        return _ler(alertas_atuais)

    return app
