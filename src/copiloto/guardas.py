"""Guardas: dado suspeito → alerta e nada é sugerido (ver docs/CONTEXTO.md, anomalias XP Demo).

Horário do servidor (XP) = horário local BRT (observado 2026-10-19) → compara direto com datetime.now().
"""

from datetime import datetime

from copiloto.config import Config


def em_pregao(cfg: Config, agora: datetime) -> bool:
    p = cfg.pregao
    return agora.weekday() < 5 and p.abertura <= agora.time() <= p.fechamento


def cotacao_viva(cfg: Config, simbolo: dict, agora: datetime) -> bool:
    """Fora do pregão não há tick novo → só exige que exista preço."""
    if not simbolo.get("existe") or not (simbolo.get("ask") or simbolo.get("ultimo")):
        return False
    if not em_pregao(cfg, agora):
        return True
    h = simbolo.get("horario_cotacao")
    return bool(h) and (agora - datetime.fromisoformat(h)).total_seconds() <= cfg.alertas.simbolo_sem_cotacao_s


def verificar(cfg: Config, conta: dict, posicoes: list[dict], simbolos: list[dict], agora: datetime) -> list[dict]:
    """`simbolos` deve cobrir watchlist + tickers das posições."""
    por_ticker = {s["ticker"]: s for s in simbolos}
    alertas = []
    for s in simbolos:
        if not cotacao_viva(cfg, s, agora):
            em_carteira = any(p["ticker"] == s["ticker"] for p in posicoes)
            alertas.append({"tipo": "simbolo_sem_cotacao", "ticker": s["ticker"], "em_carteira": em_carteira,
                            "horario_cotacao": s.get("horario_cotacao"),
                            "msg": "sem cotação viva → não sugerir nada" + (" (posição aberta!)" if em_carteira else "")})
    for p in posicoes:
        if p["ticker"] not in por_ticker:
            alertas.append({"tipo": "simbolo_sem_cotacao", "ticker": p["ticker"], "em_carteira": True,
                            "horario_cotacao": None, "msg": "posição em símbolo não consultado"})
    if cfg.alertas.margem_zero_com_posicao and posicoes and conta["margem"] == 0:
        alertas.append({"tipo": "margem_zero_com_posicao", "tickers": sorted({p["ticker"] for p in posicoes}),
                        "msg": "posição aberta com margem 0 ≠ risco nulo"})
    return alertas


def alertas_atuais(servico, agora: datetime | None = None) -> list[dict]:
    """Lê conta/posições/símbolos (watchlist + carteira) do serviço e aplica as guardas."""
    posicoes = servico.posicoes()
    tickers = list(dict.fromkeys(servico.cfg.universo.watchlist + [p["ticker"] for p in posicoes]))
    return verificar(servico.cfg, servico.conta(), posicoes, servico.simbolos(tickers), agora or datetime.now())
