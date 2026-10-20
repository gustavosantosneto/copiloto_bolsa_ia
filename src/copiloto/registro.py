"""Registro de deals → dados/{conta}_historico_trades.csv (1 linha por deal, append imediato)."""

import csv
import os
import time
from datetime import date, timedelta
from pathlib import Path

from copiloto.config import RAIZ, Config

COLUNAS = [
    "data_hora", "ticker", "tipo", "entrada", "qtd", "preco",
    "ticket_deal", "ticket_ordem", "ticket_posicao",
    "resultado_bruto", "custos", "resultado_liquido",
    "saldo_antes", "saldo_depois", "patrimonio_antes", "patrimonio_depois",
    "margem_antes", "margem_depois", "margem_livre_antes", "margem_livre_depois",
    "nivel_margem_antes", "nivel_margem_depois", "margem_prevista_mt5",
    "deals_no_ciclo", "hora_snapshot_antes", "hora_snapshot_depois",
    "conta", "ambiente", "fonte", "status", "obs", "motivo",
]
COLUNAS_SEM_MOTIVO = COLUNAS[:-1]  # formato até 2026-10-20 → migra ao abrir
SNAP = ("saldo", "patrimonio", "margem", "margem_livre", "nivel_margem")


def arquivo(cfg: Config, chave: str, conta: int | None = None) -> Path:
    """Arquivo da conta (`{conta}` no caminho de [registro]); sem conta → login do .env."""
    return RAIZ / getattr(cfg.registro, chave).format(conta=conta or cfg.credenciais.login)


class Registro:
    def __init__(self, cfg: Config, conta: int, caminho: Path | None = None):
        self.caminho = caminho or arquivo(cfg, "csv_historico", conta)
        self.conta, self.ambiente = conta, cfg.geral.ambiente
        self.tickets = self._tickets_gravados()

    def _tickets_gravados(self) -> set[int]:
        if not self.caminho.exists() or self.caminho.stat().st_size == 0:
            with open(self.caminho, "w", newline="", encoding="utf-8") as f:
                csv.writer(f, delimiter=";").writerow(COLUNAS)
            return set()
        with open(self.caminho, newline="", encoding="utf-8") as f:
            leitor = csv.DictReader(f, delimiter=";")
            linhas = list(leitor)
        if leitor.fieldnames == COLUNAS_SEM_MOTIVO:
            self._reescrever(linhas)  # motivo vazio; importar() completa com o MT5
        elif leitor.fieldnames != COLUNAS:
            raise ValueError(f"{self.caminho.name}: cabeçalho diferente do esperado")
        return {int(r["ticket_deal"]) for r in linhas if r["ticket_deal"]}

    def _reescrever(self, linhas: list[dict]) -> None:
        tmp = self.caminho.with_suffix(".tmp")
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, COLUNAS, delimiter=";", restval="")
            w.writeheader()
            w.writerows(linhas)
        for tentativa in range(5):  # Windows: leitor (API) com o arquivo aberto bloqueia a troca por instantes
            try:
                os.replace(tmp, self.caminho)  # troca atômica: arquivo nunca fica pela metade
                return
            except PermissionError:
                if tentativa == 4:
                    raise
                time.sleep(0.2)

    def _linha(self, d: dict, fonte: str, evento: dict | None = None) -> dict:
        custos = d["comissao"] + d["taxa"] + d["swap"]  # MT5: custo vem negativo
        linha = {
            "data_hora": d["horario"], "ticker": d["ticker"], "tipo": d["tipo"], "entrada": d["entrada"],
            "qtd": d["volume"], "preco": d["preco"],
            "ticket_deal": d["ticket"], "ticket_ordem": d["ordem"], "ticket_posicao": d["posicao"],
            "resultado_bruto": d["lucro"], "custos": custos, "resultado_liquido": d["lucro"] + custos,
            "conta": self.conta, "ambiente": self.ambiente, "fonte": fonte, "status": "observado",
            "motivo": d.get("motivo", ""),
        }
        if evento:
            a, b = evento["snapshot_antes"], evento["snapshot_depois"]
            for k in SNAP:
                linha[f"{k}_antes"], linha[f"{k}_depois"] = a[k], b[k]
            linha |= {"margem_prevista_mt5": evento["margem_prevista_mt5"], "deals_no_ciclo": evento["deals_no_ciclo"],
                      "hora_snapshot_antes": a["horario"], "hora_snapshot_depois": b["horario"]}
        else:
            linha["obs"] = "importado do histórico MT5, sem snapshot"
        return linha

    def _gravar(self, linhas: list[dict]) -> int:
        novas = [l for l in linhas if l["ticket_deal"] not in self.tickets]
        if novas:
            with open(self.caminho, "a", newline="", encoding="utf-8") as f:  # fecha = flush no disco
                csv.DictWriter(f, COLUNAS, delimiter=";").writerows(novas)
            self.tickets |= {l["ticket_deal"] for l in novas}
        return len(novas)

    def importar(self, deals: list[dict]) -> int:
        """Deals do histórico MT5 que ainda não estão no CSV (sem snapshot) + completa `motivo` vazio."""
        ordenados = sorted((d for d in deals if d["tipo"] in ("compra", "venda")), key=lambda d: d["horario"])
        self._completar_motivos({d["ticket"]: d.get("motivo") for d in ordenados})
        return self._gravar([self._linha(d, "mt5_historico") for d in ordenados])

    def _completar_motivos(self, motivos: dict[int, str | None]) -> None:
        with open(self.caminho, newline="", encoding="utf-8") as f:
            linhas = list(csv.DictReader(f, delimiter=";"))
        mudou = False
        for l in linhas:
            m = motivos.get(int(l["ticket_deal"])) if l["ticket_deal"] else None
            if m and not l["motivo"]:
                l["motivo"], mudou = m, True
        if mudou:
            self._reescrever(linhas)

    def gravar_evento(self, evento: dict) -> int:
        """Evento `deal` do coletor (com snapshot antes/depois)."""
        if evento.get("evento") != "deal" or evento["deal"]["tipo"] not in ("compra", "venda"):
            return 0
        return self._gravar([self._linha(evento["deal"], "coletor", evento)])


TEXTO = {"data_hora", "ticker", "tipo", "entrada", "hora_snapshot_antes", "hora_snapshot_depois", "ambiente", "fonte",
         "status", "obs", "motivo"}
INTEIRO = {"ticket_deal", "ticket_ordem", "ticket_posicao", "deals_no_ciclo", "conta"}


def _valor(k: str, v: str):
    if v == "":
        return None
    return v if k in TEXTO else int(float(v)) if k in INTEIRO else float(v)


def ler(cfg: Config, dias: int | None = 1, caminho: Path | None = None) -> list[dict]:
    """Deals gravados nos últimos N dias (hoje = 1; None = tudo), mais recente primeiro; vazio → None."""
    caminho = caminho or arquivo(cfg, "csv_historico")
    if not caminho.exists():
        return []
    desde = (date.today() - timedelta(days=dias - 1)).isoformat() if dias else ""
    with open(caminho, newline="", encoding="utf-8") as f:
        linhas = [r for r in csv.DictReader(f, delimiter=";") if r["data_hora"] >= desde]
    return [{k: _valor(k, v) for k, v in r.items()} for r in reversed(linhas)]
