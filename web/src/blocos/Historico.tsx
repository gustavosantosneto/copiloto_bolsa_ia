// Bloco 4 — Deals do dia (CSV do coletor) + margem antes/depois
import type { Deal } from "../api";
import { brl, hora, inteiro, num, sinal } from "../formato";

export function Historico({ deals }: { deals?: Deal[] }) {
  const resultado = deals?.reduce((s, d) => s + (d.entrada === "entrada" ? 0 : d.resultado_liquido), 0) ?? 0;
  return (
    <section className="bloco">
      <h2>
        Deals de hoje ({deals?.length ?? 0}) · realizado <span className={sinal(resultado)}>{brl(resultado)}</span>
      </h2>
      <table>
        <thead>
          <tr>
            <th>Hora</th><th>Ativo</th><th>Tipo</th><th>Qtd</th><th>Preço</th><th>Resultado</th>
            <th>Margem antes → depois</th><th>Prevista MT5</th><th>Fonte</th>
          </tr>
        </thead>
        <tbody>
          {deals?.map((d) => (
            <tr key={d.ticket_deal}>
              <td>{hora(d.data_hora)}</td>
              <td>{d.ticker}</td>
              <td className={d.tipo}>{d.tipo} · {d.entrada}</td>
              <td>{inteiro(d.qtd)}</td>
              <td>{num(d.preco)}</td>
              <td className={sinal(d.resultado_liquido)}>{d.entrada === "entrada" ? "" : brl(d.resultado_liquido)}</td>
              <td>{d.margem_antes == null ? "—" : `${num(d.margem_antes)} → ${num(d.margem_depois)}`}</td>
              <td>{num(d.margem_prevista_mt5)}</td>
              <td className="sub">{d.fonte === "coletor" ? "ao vivo" : "importado"}</td>
            </tr>
          ))}
          {!deals?.length && <tr><td colSpan={9} className="vazio">Nenhum deal hoje</td></tr>}
        </tbody>
      </table>
    </section>
  );
}
