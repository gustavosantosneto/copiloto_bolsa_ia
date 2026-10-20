// Bloco 3 — Capacidade operacional: lotes padrão operáveis por ativo e o limite que trava
import type { Capacidade as TCap } from "../api";
import { brl, inteiro, num, sinal } from "../formato";

const ROTULO: Record<string, string> = {
  margem_livre: "margem livre", margem_usada_max: "margem usada máx.", max_lotes_ativo: "máx. lotes/ativo",
  max_posicoes: "máx. posições", perda_aberta_ativo: "perda aberta ativo", perda_aberta_total: "perda aberta total",
  sem_cotacao: "sem cotação", sem_margem: "sem margem",
};

export function Capacidade({ cap }: { cap?: TCap }) {
  return (
    <section className="bloco">
      <h2>Capacidade operacional {cap?.modo === "simulado" && <span className="sub">simulada</span>}</h2>
      <table>
        <thead>
          <tr>
            <th>Ativo</th><th>Preço</th><th>Carteira</th><th>P&L</th><th>Folga perda</th>
            <th>Margem/lote</th><th>Lotes</th><th>Limitado por</th>
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
              <td className="forte">{a.lotes_operaveis}</td>
              <td className="sub">{ROTULO[a.restricao] ?? a.restricao}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {!!cap?.ignoradas_fora_universo.length && (
        <div className="sub">Fora da watchlist, ignoradas na simulação: {cap.ignoradas_fora_universo.join(", ")}</div>
      )}
    </section>
  );
}
