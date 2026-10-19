"""API somente leitura (GET) — mesmos recursos da CLI. Painel web consome daqui."""

import threading
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from copiloto.capacidade import calcular
from copiloto.config import carregar_config
from copiloto.guardas import alertas_atuais
from copiloto.mt5_servico import ErroMT5, ServicoMT5


def criar_app(fabrica: Callable[[], ServicoMT5] = lambda: ServicoMT5(carregar_config())) -> FastAPI:
    estado: dict = {}
    trava = threading.Lock()  # SDK MT5 é global ao processo → 1 chamada por vez

    @asynccontextmanager
    async def ciclo_de_vida(_app):
        estado["s"] = fabrica()
        try:
            estado["s"].conectar()
        except ErroMT5:
            pass  # sobe mesmo sem MT5; 1ª requisição tenta de novo
        yield

    app = FastAPI(title="copiloto_bolsa_ia", description="Somente leitura. Nenhuma ordem é enviada.",
                  lifespan=ciclo_de_vida)

    def _ler(funcao: Callable[[ServicoMT5], object]):
        s = estado["s"]
        with trava:
            try:
                return funcao(s)
            except ErroMT5:
                try:  # conexão caiu → reconecta 1x e repete
                    s.conectar()
                    return funcao(s)
                except ErroMT5 as e:
                    raise HTTPException(503, f"MT5 indisponível: {e}") from e

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

    @app.get("/alertas")
    def alertas():
        return _ler(alertas_atuais)

    return app
