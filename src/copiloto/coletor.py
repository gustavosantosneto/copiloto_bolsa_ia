"""Coletor: poll do MT5 → eventos por diff (SDK não tem listener).

Ordem do ciclo: conta → deals/posições/ordens.
snapshot_antes = conta do ciclo anterior (lida antes do último diff sem o deal → limpa, ≤1 ciclo de defasagem).
snapshot_depois = conta relida logo após detectar o deal.
"""

import time
from collections.abc import Callable, Iterator
from datetime import datetime

from copiloto.config import Config
from copiloto.mt5_servico import ErroMT5, ServicoMT5

CAMPOS_POSICAO = ("volume", "preco_medio", "sl", "tp")
CAMPOS_ORDEM = ("volume_atual", "preco", "sl", "tp")


def _agora() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def _snapshot(conta: dict) -> dict:
    return {"horario": _agora(), **{k: conta[k] for k in ("saldo", "patrimonio", "margem", "margem_livre", "nivel_margem")}}


def _diff(tipo: str, antigos: dict[int, dict], novos: dict[int, dict], campos: tuple[str, ...]) -> list[dict]:
    eventos = [{"evento": f"{tipo}_aberta", tipo: novos[t]} for t in novos.keys() - antigos.keys()]
    eventos += [{"evento": f"{tipo}_encerrada", tipo: antigos[t]} for t in antigos.keys() - novos.keys()]
    for t in novos.keys() & antigos.keys():
        mudou = {c: [antigos[t][c], novos[t][c]] for c in campos if antigos[t][c] != novos[t][c]}
        if mudou:
            eventos.append({"evento": f"{tipo}_alterada", tipo: novos[t], "mudancas": mudou})
    return eventos


class Coletor:
    def __init__(self, servico: ServicoMT5, cfg: Config):
        self.s, self.cfg = servico, cfg
        self.conta: dict | None = None
        self.deals: set[int] = set()
        self.posicoes: dict[int, dict] = {}
        self.ordens: dict[int, dict] = {}

    def ciclo(self) -> list[dict]:
        """Um poll. 1º ciclo = linha de base, sem eventos."""
        conta = self.s.conta()
        deals = {d["ticket"]: d for d in self.s.deals(dias=1)}
        posicoes = {p["ticket"]: p for p in self.s.posicoes()}
        ordens = {o["ticket"]: o for o in self.s.ordens()}

        eventos: list[dict] = []
        if self.conta is not None:
            novos = [deals[t] for t in sorted(deals.keys() - self.deals)]
            if novos:
                antes, depois = _snapshot(self.conta), _snapshot(self.s.conta())
                eventos += [{"evento": "deal", "deal": d, "deals_no_ciclo": len(novos),
                             "snapshot_antes": antes, "snapshot_depois": depois,
                             "margem_prevista_mt5": self._margem_prevista(d)} for d in novos]
            eventos += _diff("posicao", self.posicoes, posicoes, CAMPOS_POSICAO)
            eventos += _diff("ordem", self.ordens, ordens, CAMPOS_ORDEM)

        self.conta, self.posicoes, self.ordens = conta, posicoes, ordens
        self.deals |= deals.keys()  # união: deal que sai da janela de 1 dia não reaparece como novo
        return [{"horario_detectado": _agora(), **e} for e in eventos]

    def _margem_prevista(self, d: dict) -> float | None:
        if d["tipo"] not in ("compra", "venda"):
            return None
        return self.s.margem_prevista(d["ticker"], d["tipo"], d["volume"], d["preco"])

    def intervalo(self) -> float:
        p, agora = self.cfg.pregao, datetime.now()
        em_pregao = agora.weekday() < 5 and p.abertura <= agora.time() <= p.fechamento
        c = self.cfg.coletor
        return c.intervalo_poll_s if em_pregao else c.intervalo_poll_fora_pregao_s

    def rodar(self, ciclos: int | None = None, dormir: Callable[[float], None] = time.sleep) -> Iterator[dict]:
        """Gera eventos para sempre (ou N ciclos). Erro MT5 → reconecta e segue."""
        n = 0
        while ciclos is None or n < ciclos:
            n += 1
            try:
                yield from self.ciclo()
            except ErroMT5 as e:
                yield {"horario_detectado": _agora(), "evento": "erro_mt5", "erro": str(e)}
                try:
                    self.s.conectar()
                except ErroMT5:
                    pass  # próximo ciclo tenta de novo
            dormir(self.intervalo())
