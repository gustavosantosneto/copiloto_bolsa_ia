"""CLI `copiloto` — mesmos comandos para humano e agente."""

import json

import typer

from copiloto.capacidade import calcular
from copiloto.coletor import Coletor
from copiloto.config import Config, ErroConfig, carregar_config
from copiloto.mt5_servico import ErroMT5, ServicoMT5
from copiloto.registro import Registro

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.callback()
def main():
    """Copiloto de trading MT5."""


def _cfg() -> Config:
    try:
        return carregar_config()
    except ErroConfig as e:
        typer.echo(f"ERRO config: {e}", err=True)
        raise typer.Exit(1)


def _json(dados) -> None:
    typer.echo(json.dumps(dados, indent=2, ensure_ascii=False))


def _ler_mt5(metodo: str, **kw) -> None:
    try:
        with ServicoMT5(_cfg()) as s:
            _json(getattr(s, metodo)(**kw))
    except ErroMT5 as e:
        typer.echo(f"ERRO MT5: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def config():
    """Mostra a config efetiva (senha mascarada)."""
    cfg = _cfg()
    dados = cfg.model_dump(mode="json")  # SecretStr → "**********"
    dados["credenciais"]["completas"] = cfg.credenciais.completas
    _json(dados)
    if not cfg.credenciais.completas:
        amb = cfg.geral.ambiente.upper()
        typer.echo(f"AVISO: credenciais MT5_{amb}_* incompletas no .env", err=True)


@app.command()
def conta():
    """Saldo, patrimônio, margem, margem livre, nível de margem."""
    _ler_mt5("conta")


@app.command()
def posicoes():
    """Posições abertas."""
    _ler_mt5("posicoes")


@app.command()
def ordens():
    """Ordens pendentes."""
    _ler_mt5("ordens")


@app.command()
def historico(dias: int = typer.Option(None, help="padrão: coletor.historico_deals_dias")):
    """Deals dos últimos N dias."""
    _ler_mt5("deals", dias=dias)


@app.command()
def simbolos(tickers: list[str] = typer.Argument(None, help="padrão: watchlist")):
    """Info e última cotação dos símbolos."""
    _ler_mt5("simbolos", tickers=[t.upper() for t in tickers] if tickers else None)


@app.command()
def coletar(ciclos: int = typer.Option(None, help="padrão: infinito (Ctrl+C para parar)")):
    """Poll do MT5; grava deals no CSV na hora e imprime 1 evento JSON por linha."""
    try:
        with ServicoMT5(_cfg()) as s:
            reg = Registro(s.cfg, s.conta()["login"])
            n = reg.importar(s.deals())
            typer.echo(f"{reg.caminho.name}: {n} deals importados do histórico MT5", err=True)
            for e in Coletor(s, s.cfg).rodar(ciclos):
                reg.gravar_evento(e)
                typer.echo(json.dumps(e, ensure_ascii=False))
    except ErroMT5 as e:
        typer.echo(f"ERRO MT5: {e}", err=True)
        raise typer.Exit(1)
    except KeyboardInterrupt:
        pass


@app.command()
def capacidade():
    """Lotes padrão operáveis por ativo da watchlist e o limite que trava cada um."""
    try:
        with ServicoMT5(_cfg()) as s:
            _json(calcular(s.cfg, s.conta(), s.posicoes(), s.simbolos(),
                           lambda t, v, p: s.margem_prevista(t, "compra", v, p)))
    except ErroMT5 as e:
        typer.echo(f"ERRO MT5: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def api():
    """Sobe a API somente leitura (host/porta em [api])."""
    import uvicorn

    from copiloto.api import criar_app

    cfg = _cfg()
    uvicorn.run(criar_app(), host=cfg.api.host, port=cfg.api.porta)
