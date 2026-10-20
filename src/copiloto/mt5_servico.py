"""Serviço MT5 — único ponto de contato com o SDK. Somente leitura (V1)."""

import time
from datetime import UTC, datetime, timedelta

import MetaTrader5 as mt5

from copiloto.config import Config

MODO_CONTA = {0: "demo", 1: "contest", 2: "real"}
DIRECAO_POSICAO = {0: "compra", 1: "venda"}
TIPO_ORDEM = {
    0: "compra", 1: "venda", 2: "compra_limite", 3: "venda_limite", 4: "compra_stop",
    5: "venda_stop", 6: "compra_stop_limite", 7: "venda_stop_limite", 8: "fechamento_por",
}
TIPO_DEAL = {0: "compra", 1: "venda", 2: "saldo", 3: "credito", 4: "encargo", 5: "correcao", 6: "bonus", 7: "comissao"}
ENTRADA_DEAL = {0: "entrada", 1: "saida", 2: "inversao", 3: "saida_por"}


class ErroMT5(Exception):
    pass


def _hora(segundos: float) -> str:
    # SDK devolve epoch no fuso do servidor → ISO sem fuso (= horário do servidor)
    return datetime.fromtimestamp(segundos, UTC).replace(tzinfo=None).isoformat(timespec="milliseconds")


def _erro(acao: str) -> ErroMT5:
    return ErroMT5(f"{acao}: {mt5.last_error()}")


class ServicoMT5:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def __enter__(self):
        self.conectar()
        return self

    def __exit__(self, *_):
        mt5.shutdown()

    def conectar(self, tentativas: int | None = None) -> None:
        c, m = self.cfg.credenciais, self.cfg.mt5
        tentativas = m.tentativas_reconexao if tentativas is None else tentativas
        if not c.completas:
            raise ErroMT5(f"credenciais MT5_{self.cfg.geral.ambiente.upper()}_* incompletas no .env")
        assert c.senha  # completas garante
        args = dict(login=c.login, password=c.senha.get_secret_value(), server=c.servidor, timeout=m.timeout_conexao_ms)
        if m.caminho_terminal:
            args["path"] = m.caminho_terminal
        for tentativa in range(tentativas + 1):
            if mt5.initialize(**args):
                return self._checa_ambiente()
            erro = _erro("initialize")
            if tentativa == tentativas:
                raise erro
            time.sleep(m.intervalo_reconexao_s)

    def _checa_ambiente(self) -> None:
        # Guarda: conta logada tem que bater com geral.ambiente (demo ≠ real)
        info = mt5.account_info()
        if info is None:
            mt5.shutdown()
            raise _erro("account_info")
        modo = MODO_CONTA.get(info.trade_mode, str(info.trade_mode))
        if (modo == "real") != (self.cfg.geral.ambiente == "real"):
            mt5.shutdown()
            raise ErroMT5(f"conta logada é '{modo}', config pede '{self.cfg.geral.ambiente}'")

    def conta(self) -> dict:
        a = mt5.account_info()
        if a is None:
            raise _erro("account_info")
        return {
            "login": a.login, "servidor": a.server, "corretora": a.company, "moeda": a.currency,
            "modo": MODO_CONTA.get(a.trade_mode, str(a.trade_mode)),
            "saldo": a.balance, "patrimonio": a.equity, "margem": a.margin, "margem_livre": a.margin_free,
            "nivel_margem": a.margin_level, "lucro_aberto": a.profit,
            "alavancagem_declarada": a.leverage, "negociacao_permitida": a.trade_allowed,
        }

    def posicoes(self) -> list[dict]:
        r = mt5.positions_get()
        if r is None:
            raise _erro("positions_get")
        return [{
            "ticket": p.ticket, "ticker": p.symbol, "direcao": DIRECAO_POSICAO.get(p.type, str(p.type)),
            "volume": p.volume, "preco_medio": p.price_open, "preco_atual": p.price_current,
            "sl": p.sl, "tp": p.tp, "lucro": p.profit, "swap": p.swap,
            "abertura": _hora(p.time_msc / 1000), "magic": p.magic, "comentario": p.comment,
        } for p in r]

    def ordens(self) -> list[dict]:
        r = mt5.orders_get()
        if r is None:
            raise _erro("orders_get")
        return [{
            "ticket": o.ticket, "ticker": o.symbol, "tipo": TIPO_ORDEM.get(o.type, str(o.type)),
            "volume_inicial": o.volume_initial, "volume_atual": o.volume_current,
            "preco": o.price_open, "sl": o.sl, "tp": o.tp,
            "colocada": _hora(o.time_setup_msc / 1000), "comentario": o.comment,
        } for o in r]

    def deals(self, dias: int | None = None) -> list[dict]:
        dias = dias or self.cfg.coletor.historico_deals_dias
        ate = datetime.now() + timedelta(days=1)  # folga: horário do servidor pode estar à frente
        r = mt5.history_deals_get(ate - timedelta(days=dias + 1), ate)
        if r is None:
            raise _erro("history_deals_get")
        return [{
            "ticket": d.ticket, "ordem": d.order, "posicao": d.position_id, "ticker": d.symbol,
            "tipo": TIPO_DEAL.get(d.type, str(d.type)), "entrada": ENTRADA_DEAL.get(d.entry, str(d.entry)),
            "volume": d.volume, "preco": d.price, "comissao": d.commission, "taxa": d.fee,
            "swap": d.swap, "lucro": d.profit, "horario": _hora(d.time_msc / 1000), "comentario": d.comment,
        } for d in r]

    def simbolos(self, tickers: list[str] | None = None) -> list[dict]:
        """Info + última cotação; símbolo inexistente vem com existe=False (não quebra)."""
        saida = []
        for t in tickers or self.cfg.universo.watchlist:
            s = mt5.symbol_info(t)
            if s is None:
                saida.append({"ticker": t, "existe": False})
                continue
            k = mt5.symbol_info_tick(t)
            saida.append({
                "ticker": t, "existe": True, "visivel": s.visible,
                "bid": k.bid if k else None, "ask": k.ask if k else None, "ultimo": k.last if k else None,
                "horario_cotacao": _hora(k.time_msc / 1000) if k and k.time_msc else None,
                "lote_min": s.volume_min, "passo_lote": s.volume_step, "tamanho_contrato": s.trade_contract_size,
                "margem_inicial": s.margin_initial, "modo_calculo": s.trade_calc_mode,
            })
        return saida

    def margem_prevista(self, ticker: str, tipo: str, volume: float, preco: float) -> float | None:
        """Margem que o MT5 calcula (order_calc_margin) — só cálculo, não envia nada."""
        acao = mt5.ORDER_TYPE_BUY if tipo == "compra" else mt5.ORDER_TYPE_SELL
        return mt5.order_calc_margin(acao, ticker, volume, preco)
