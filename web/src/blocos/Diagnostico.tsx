// Diagnóstico (modo do card Resultado): MAE/MFE das operações encerradas. Estudo, nunca sinal. Poll lento (cálculo pesado).
import { usePoll, type Diagnostico as TDiag } from "../api";
import { brl, num, sinal } from "../formato";

const MIN_MS = 60_000;
const MOTIVO: Record<string, string> = { tp: "TP", sl: "SL", manual: "manual", mobile: "celular", web: "web", robo: "robô" };

export function Diagnostico() {
  const { dados: d, erro } = usePoll<TDiag>("/diagnostico?dias=30", MIN_MS);
  if (!d) return <div className="vazio">{erro ?? "Calculando…"}</div>;
  const r = d.resumo;
  const item = (rotulo: string, valor: string, classe = "") => (
    <div className="item"><span className="rotulo">{rotulo}</span><span className={`valor ${classe}`}>{valor}</span></div>
  );
  return (
    <>
      <div className="grade">
        {item("Operações", `${r.com_ticks}${r.sem_ticks ? ` (+${r.sem_ticks} s/ ticks)` : ""}`)}
        {item("MAE mediana", brl(r.mae_mediana), "neg")}
        {item("MAE 10% piores", brl(r.mae_p10), "neg")}
        {item("Pior MAE", brl(r.mae_pior), "neg")}
        {item("MFE mediana", brl(r.mfe_mediana), "pos")}
        {item("Duração mediana", r.duracao_mediana_min == null ? "—" : `${num(r.duracao_mediana_min, 0)} min`)}
      </div>
      <div className="sub">
        {Object.entries(r.por_motivo).map(([m, g]) => `${MOTIVO[m] ?? m}: ${g.n} · média ${brl(g.resultado_medio)} · MAE ${brl(g.mae_mediana)}`).join("  |  ")}
      </div>
      <table>
        <thead>
          <tr><th>Data</th><th>Ativo</th><th>Lado</th><th>Qtd</th><th>Resultado</th><th>MAE</th><th>MFE</th><th>Até MAE</th><th>Duração</th><th>Saída</th></tr>
        </thead>
        <tbody>
          {d.operacoes.map((o) => (
            <tr key={`${o.ticker}${o.abertura}`} className={o.status === "ok" ? "" : "travado"}>
              <td>{o.abertura.slice(5, 16).replace("T", " ")}</td>
              <td>{o.ticker}</td>
              <td className={o.lado}>{o.lado}</td>
              <td>{num(o.qtd_max, 0)}</td>
              <td className={sinal(o.resultado_bruto)}>{brl(o.resultado_bruto)}</td>
              <td className="neg">{o.status === "ok" ? brl(o.mae) : "sem ticks"}</td>
              <td className="pos">{brl(o.mfe)}</td>
              <td>{o.min_ate_mae == null ? "—" : `${num(o.min_ate_mae, 0)} min`}</td>
              <td>{num(o.duracao_min, 0)} min</td>
              <td>{o.motivo_saida ? (MOTIVO[o.motivo_saida] ?? o.motivo_saida) : "—"}</td>
            </tr>
          ))}
          {!d.operacoes.length && <tr><td colSpan={10} className="vazio">Nenhuma operação encerrada</td></tr>}
        </tbody>
      </table>
      <div className="sub">{r.limites} · 30 dias · ticks via `copiloto mercado`</div>
    </>
  );
}
