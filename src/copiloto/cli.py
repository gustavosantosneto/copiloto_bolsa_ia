"""CLI `copiloto` — mesmos comandos para humano e agente."""

import json

import typer

from copiloto.config import ErroConfig, carregar_config

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.callback()
def main():
    """Copiloto de trading MT5."""


@app.command()
def config():
    """Mostra a config efetiva (senha mascarada)."""
    try:
        cfg = carregar_config()
    except ErroConfig as e:
        typer.echo(f"ERRO config: {e}", err=True)
        raise typer.Exit(1)

    dados = cfg.model_dump(mode="json")  # SecretStr → "**********"
    dados["credenciais"]["completas"] = cfg.credenciais.completas
    typer.echo(json.dumps(dados, indent=2, ensure_ascii=False))
    if not cfg.credenciais.completas:
        amb = cfg.geral.ambiente.upper()
        typer.echo(f"AVISO: credenciais MT5_{amb}_* incompletas no .env", err=True)
