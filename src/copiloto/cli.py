"""CLI `copiloto` — mesmos comandos para humano e agente."""

import json
import sys

import typer

from copiloto import corretoras as corr, diagnostico as diag, medicao, mercado as merc, negocios, resultado as res
from copiloto import similaridade as simil, spread as sprd
from copiloto.capacidade import calcular
from copiloto.coletor import Coletor
from copiloto.guardas import atencoes_atuais
from copiloto.config import Config, ErroConfig, carregar_config
from copiloto.mt5_servico import ErroMT5, ServicoMT5
from copiloto.registro import Registro, ler

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.callback()
def main():
    """Copiloto de trading MT5."""
    sys.stdout.reconfigure(encoding="utf-8")  # console Windows (cp1252) quebra com →, ≥, Δ


def _cfg() -> Config:
    try:
        return carregar_config()
    except ErroConfig as e:
        typer.echo(f"ERRO config: {e}", err=True)
        raise typer.Exit(1)


def _json(dados) -> None:
    typer.echo(json.dumps(dados, indent=2, ensure_ascii=False))


def _ler_mt5_com(funcao) -> None:
    try:
        with ServicoMT5(_cfg()) as s:
            _json(funcao(s))
    except ErroMT5 as e:
        typer.echo(f"ERRO MT5: {e}", err=True)
        raise typer.Exit(1)


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
def atencoes():
    """Guardas (sem cotação viva, margem zero) + limites de risco e divergência de margem."""
    try:
        with ServicoMT5(_cfg()) as s:
            _json(atencoes_atuais(s))
    except ErroMT5 as e:
        typer.echo(f"ERRO MT5: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def registro(dias: int = typer.Option(1, help="1 = hoje")):
    """Deals gravados no CSV (com snapshot antes/depois), mais recente primeiro."""
    _json(ler(_cfg(), dias))


@app.command()
def coletar(ciclos: int = typer.Option(None, help="padrão: infinito (Ctrl+C para parar)")):
    """Poll do MT5; grava deals no CSV na hora e imprime 1 evento JSON por linha."""
    try:
        with ServicoMT5(_cfg()) as s:
            login = s.conta()["login"]
            reg = Registro(s.cfg, login)
            n = reg.importar(s.deals())
            typer.echo(f"{reg.caminho.name}: {n} deals importados do histórico MT5", err=True)
            medicao.gravar_base(s.cfg, login)
            for e in Coletor(s, s.cfg).rodar(ciclos):
                if reg.gravar_evento(e):
                    medicao.gravar_base(s.cfg, login)  # deal com snapshot → nova medição
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
def base():
    """Regera e mostra a base operacional da conta (margem/alavancagem medidas por ativo)."""
    cfg = _cfg()
    typer.echo(f"{medicao.gravar_base(cfg).name} atualizado", err=True)
    _json(medicao.consolidar(cfg, ler(cfg, None)))


@app.command()
def resultado(dias: int = typer.Option(30, help="1 = hoje")):
    """Resultado realizado: bruto, custos, líquido, médias por operação/dia, drawdown."""
    cfg = _cfg()
    _json(res.calcular(cfg, ler(cfg, dias)))


@app.command()
def corretoras():
    """Cadastro de corretoras + capacidade e custo de 1 lote day trade em cada uma."""
    try:
        with ServicoMT5(_cfg()) as s:
            _json(corr.simular(s.cfg, s.conta(), s.posicoes(), s.simbolos()))
    except ErroMT5 as e:
        typer.echo(f"ERRO MT5: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def mercado():
    """Candles M1 + negócios tick a tick da watchlist p/ estudo (data/mercado/): 1ª vez = dias_iniciais, depois incremental."""
    try:
        with ServicoMT5(_cfg()) as s:
            _json({"candles": merc.atualizar(s, s.cfg), "negocios": negocios.atualizar(s, s.cfg)})
    except ErroMT5 as e:
        typer.echo(f"ERRO MT5: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def diagnostico(dias: int = typer.Option(30, help="1 = hoje")):
    """MAE/MFE das operações encerradas (negócios gravados por `copiloto mercado`). Estudo, nunca sinal."""
    cfg = _cfg()
    _json(diag.calcular(cfg, ler(cfg, dias)))


@app.command()
def similaridade():
    """Calcula matriz de similaridade, atraso, cointegração e Granger (M1 gravado) → [similaridade].arquivo. Estudo, nunca sinal."""
    cfg = _cfg()
    typer.echo(f"{simil.gravar(cfg)} atualizado", err=True)
    d = simil.ler(cfg)
    _json({"amostra": d["amostra"], "pares_mais_fortes": d["pares"][:10], "atrasos": d["atrasos"][:10]})


@app.command()
def spread():
    """Spread atual × média/desvio do ativo (M1 gravado). Só atenção, nunca decisivo."""
    _ler_mt5_com(lambda s: sprd.avaliar(s.cfg, s.simbolos()))


@app.command()
def api():
    """Sobe a API somente leitura (host/porta em [api])."""
    import uvicorn

    from copiloto.api import criar_app

    cfg = _cfg()
    uvicorn.run(criar_app(), host=cfg.api.host, port=cfg.api.porta)


@app.command()
def painel():
    """Sobe coletor + API + web (Vite) juntos. Ctrl+C encerra tudo. Portas: [api].porta, [painel].porta_web."""
    import os
    import shutil
    import subprocess
    import time

    from copiloto.config import RAIZ

    cfg = _cfg()  # falha cedo se config inválida
    npm = shutil.which("npm")
    if not npm:
        typer.echo("ERRO: npm não encontrado (instale Node.js)", err=True)
        raise typer.Exit(1)
    web = RAIZ / "web"
    if not (web / "node_modules").exists():
        subprocess.run([npm, "install"], cwd=web, check=True)
    (RAIZ / "logs").mkdir(exist_ok=True)
    eventos = open(RAIZ / "logs" / "eventos.jsonl", "a", encoding="utf-8")
    copiloto = [sys.executable, "-m", "copiloto.cli"]
    processos = {
        "coletor": subprocess.Popen([*copiloto, "coletar"], stdout=eventos),
        "api": subprocess.Popen([*copiloto, "api"]),
        "web": subprocess.Popen([npm, "run", "dev"], cwd=web, env=os.environ | {
            "COPILOTO_API": f"http://{cfg.api.host}:{cfg.api.porta}", "COPILOTO_PORTA_WEB": str(cfg.painel.porta_web)}),
    }
    typer.echo(f"Painel: http://localhost:{cfg.painel.porta_web}  ·  eventos → logs/eventos.jsonl  ·  Ctrl+C encerra", err=True)
    try:
        while all(p.poll() is None for p in processos.values()):
            time.sleep(1)
        caiu = [n for n, p in processos.items() if p.poll() is not None]
        typer.echo(f"ERRO: processo encerrou: {', '.join(caiu)}", err=True)
    except KeyboardInterrupt:
        pass
    finally:
        for p in processos.values():
            if p.poll() is None:  # Windows: /T mata a árvore (npm → node/vite)
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True) if sys.platform == "win32"                     else p.terminate()
        eventos.close()


if __name__ == "__main__":
    app()
