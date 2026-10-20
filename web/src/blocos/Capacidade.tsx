// Bloco 3 — Capacidade operacional: lotes padrão operáveis por ativo, o limite que trava e o spread (só atenção)
import { Card } from "../Card";
import type { Capacidade as TCap, Spread } from "../api";
import { brl, inteiro, num, sinal } from "../formato";

const ROTULO: Record<string, string> = {
  margem_livre: "margem livre", margem_usada_max: "margem usada máx.", max_lotes_ativo: "máx. lotes/ativo",
  max_posicoes: "máx. posições", perda_aberta_ativo: "perda aberta ativo", perda_aberta_total: "perda aberta total",
  sem_cotacao: "sem cotação", sem_margem: "sem margem",
};

export function Capacidade({ cap, spread }: { cap?: TCap; spread?: Spread[] }) {
  const sp = Object.fromEntries((spread ?? []).map((s) => [s.ticker, s]));
  return (
    <Card id="capacidade" titulo={<>Capacidade operacional {cap?.modo === "simulado" && <span className="sub">simulada</span>}</>}>
      <table>
        <thead>
          <tr>
            <th>Ativo</th><th>Preço</th><th>Carteira</th><th>P&L</th><th>Folga perda</th>
            <th>Margem/lote</th><th>Spread</th><th>Ticks · média</th><th>Lotes</th><th>Limitado por</th>
          </tr>
        </thead>
        <tbody>
          {cap?.ativos.map((a) => (
            <tr key={a.ticker} className={a.lotes_operaveis ? "" : "travado"}>
              <td>{a.ticker}</td>
              <td>{num(a.preco)}</td>
              <td>{a.qtd_carteira ? inteiro(a.qtd_carteira) : ""}</td>
              <td className={sinal(a.lucro_aberto)}>{a.lucro_aberto ? brl(a.lucro_aberto) : ""}</td>
              <td className={a.folga_perda_ativo <= 0 ? "neg" : ""}>{brl(a.folga_perda_ativo)}</td>
              <td title={a.alavancagem_lote ? `${num(a.alavancagem_lote, 0)}x` : ""}>{brl(a.margem_lote)}</td>
              <td className={["teto", "anormal"].includes(sp[a.ticker]?.status) ? "aviso" : ""}
                  title={sp[a.ticker]?.media_pct != null ? `média ${num(sp[a.ticker].media_pct, 3)}% · ${sp[a.ticker].status}` : sp[a.ticker]?.status}>
                {sp[a.ticker]?.spread_pct == null ? "—" : `${num(sp[a.ticker].spread_pct, 3)}%`}
              </td>
              <td className="sub">{num(sp[a.ticker]?.spread_ticks, 0)} · {num(sp[a.ticker]?.media_ticks, 1)}</td>
              <td className="forte">{a.lotes_operaveis}</td>
              <td className="sub">{ROTULO[a.restricao] ?? a.restricao}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {!!cap?.ignoradas_fora_universo.length && (
        <div className="sub">Fora da watchlist, ignoradas na simulação: {cap.ignoradas_fora_universo.join(", ")}</div>
      )}
    </Card>
  );
}
