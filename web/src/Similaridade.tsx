// Página Similaridade (V2): matriz 17×17 de correlação dos retornos; opacidade = |ρ| (irrelevante quase some).
// Estudo, nunca sinal. Calculada por `copiloto similaridade`; aqui só leitura.
import { useState } from "react";
import { usePoll } from "./api";
import { num } from "./formato";

type Par = {
  a: string; b: string; bruta: number; residual: number; residual_dentro: number; residual_fora: number;
  estabilidade: number | null; coint_q: number | null; tipo: string | null;
};
type Atraso = { lider: string; seguidor: string; lag_min: number; rho: number; q: number; granger_q: number | null };
type TSim = {
  calculado_em: string; tickers: string[]; matrizes: Record<string, (number | null)[][]>; pares: Par[]; atrasos: Atraso[];
  amostra: { timeframe: string; inicio: string; fim: string; sessoes: number; candles: number; fora_amostra_desde: string };
  limites: string;
};

const BASES = { bruta: "Bruta", residual: "Sem mercado" } as const;
const PERIODOS = { total: "Janela toda", dentro: "Dentro da amostra", fora: "Fora da amostra" } as const;

export function Similaridade() {
  const { dados: d, erro } = usePoll<TSim>("/similaridade", 60_000);
  const [base, setBase] = useState<keyof typeof BASES>("residual");
  const [periodo, setPeriodo] = useState<keyof typeof PERIODOS>("total");
  if (!d) return <div className="vazio">{erro ?? "Carregando…"}</div>;
  const m = d.matrizes[`${base}_${periodo}`];
  const par = (a: string, b: string) => d.pares.find((p) => (p.a === a && p.b === b) || (p.a === b && p.b === a));
  const dica = (i: number, j: number) => {
    const p = par(d.tickers[i], d.tickers[j]);
    if (!p) return "";
    return `${p.a} × ${p.b}\nbruta ${num(p.bruta * 100, 0)}% · sem mercado ${num(p.residual * 100, 0)}%\n` +
      `dentro ${num(p.residual_dentro * 100, 0)}% → fora ${num(p.residual_fora * 100, 0)}%\n` +
      `mesmo sinal em ${num((p.estabilidade ?? 0) * 100, 0)}% das semanas · cointegração q=${num(p.coint_q, 3)}`;
  };
  const seletor = <T extends string>(opcoes: Record<T, string>, atual: T, set: (v: T) => void) => (
    <div className="abas">
      {(Object.keys(opcoes) as T[]).map((k) => (
        <button key={k} className={k === atual ? "ativa" : ""} onClick={() => set(k)}>{opcoes[k]}</button>
      ))}
    </div>
  );

  return (
    <div className="similaridade">
      <section className="bloco matriz-bloco">
        <div className="cabecalho">
          <h2>Similaridade <span className="sub">
            retornos {d.amostra.timeframe} · {d.amostra.sessoes} sessões ({d.amostra.inicio.slice(0, 10)} → {d.amostra.fim.slice(0, 10)})
            · fora da amostra desde {d.amostra.fora_amostra_desde.slice(0, 10)} · calculado {d.calculado_em.slice(0, 16).replace("T", " ")}
          </span></h2>
          {seletor(BASES, base, setBase)}
          {seletor(PERIODOS, periodo, setPeriodo)}
        </div>
        <table className="matriz">
          <thead>
            <tr><th />{d.tickers.map((t) => <th key={t}>{t}</th>)}</tr>
          </thead>
          <tbody>
            {d.tickers.map((ti, i) => (
              <tr key={ti}>
                <th>{ti}</th>
                {d.tickers.map((tj, j) => {
                  const v = m[i][j] ?? 0;
                  const forca = i === j ? 1 : Math.abs(v);
                  return (
                    <td key={tj} title={i === j ? ti : dica(i, j)}
                        className={i === j ? "diag" : v >= 0 ? "direta" : "inversa"}
                        style={{ opacity: Math.max(0.06, forca), "--forca": `${Math.round(forca * 45)}%` } as React.CSSProperties}>
                      {i === j ? "100%" : `${num(v * 100, 0)}%`}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
        <div className="sub">{d.limites}</div>
      </section>
      <aside className="bloco lista-sim">
        <h2>Quem antecipa quem <span className="sub">M1 · sem mercado · q ≤ 5%</span></h2>
        <div className="sub">ρ perto de 0 = significativo pela amostra grande, mas pouco útil (não paga spread/custo)</div>
        <div className="corpo">
          <table>
            <thead><tr><th>Líder → seguidor</th><th>Atraso</th><th>ρ</th><th>Granger q</th></tr></thead>
            <tbody>
              {d.atrasos.slice(0, 40).map((a) => (
                <tr key={`${a.lider}${a.seguidor}`} style={{ opacity: Math.max(0.35, Math.min(1, Math.abs(a.rho) * 10)) }}>
                  <td>{a.lider} → {a.seguidor}</td>
                  <td>{a.lag_min} min</td>
                  <td className={a.rho >= 0 ? "pos" : "neg"}>{num(a.rho * 100, 1)}%</td>
                  <td>{a.granger_q == null ? "—" : num(a.granger_q, 3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </aside>
    </div>
  );
}
