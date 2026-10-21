// Página Similaridade: matriz 17×17 dos últimos N minutos de pregão (ao vivo, ângulo da VWAP de cada minuto).
// Triângulo de baixo e de cima com métodos escolhidos (aproveita a simetria). Opacidade = |ρ|. Estudo, nunca sinal.
import { useState } from "react";
import { usePoll } from "./api";
import { num } from "./formato";

type TSim = {
  calculado_em: string; tickers: string[]; matrizes: Record<string, number[][]>; limites: string;
  amostra: { inicio: string; fim: string; minutos: number; desvio_max_candles: number };
};

const METODOS = {
  bruta: "Bruta", residual: "Sem mercado", angulo_corr: "Correlação ±k", angulo_razao: "Razão ±k",
} as const;
type Metodo = keyof typeof METODOS;

export function Similaridade() {
  const { dados: d, erro } = usePoll<TSim>("/similaridade", 60_000);
  const [baixo, setBaixo] = useState<Metodo>("angulo_razao");
  const [cima, setCima] = useState<Metodo>("angulo_corr");
  if (!d) return <div className="vazio">{erro ?? "Calculando…"}</div>;
  const k = (met: Metodo, i: number, j: number) => d.matrizes[`${met}_k`]?.[i]?.[j];
  const dica = (i: number, j: number) => {
    const linhas = (Object.keys(METODOS) as Metodo[]).map((met) => {
      const desl = k(met, i, j);
      return `${METODOS[met]}: ${num(d.matrizes[met][i][j] * 100, 0)}%${desl == null ? "" : ` (deslocamento ${desl > 0 ? "+" : ""}${desl} min)`}`;
    });
    return `${d.tickers[i]} × ${d.tickers[j]}\n${linhas.join("\n")}`;
  };
  const seletor = (atual: Metodo, set: (v: Metodo) => void) => (
    <div className="abas">
      {(Object.keys(METODOS) as Metodo[]).map((met) => (
        <button key={met} className={met === atual ? "ativa" : ""} onClick={() => set(met)}>{METODOS[met]}</button>
      ))}
    </div>
  );

  return (
    <div className="similaridade">
      <section className="bloco matriz-bloco">
        <div className="cabecalho">
          <h2>Similaridade <span className="sub">
            últimos {d.amostra.minutos} min de pregão ({d.amostra.inicio.slice(11, 16)} → {d.amostra.fim.slice(11, 16)}
            {" "}de {d.amostra.fim.slice(0, 10)}) · VWAP de cada minuto · ±k até {d.amostra.desvio_max_candles} min
          </span></h2>
          <span className="sub">◣ abaixo</span>{seletor(baixo, setBaixo)}
          <span className="sub">◥ acima</span>{seletor(cima, setCima)}
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
                  const v = d.matrizes[i > j ? baixo : cima][i][j] ?? 0; // ◣ abaixo da diagonal × ◥ acima
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
        <div className="sub">{d.limites} · atualiza a cada 1 min</div>
      </section>
    </div>
  );
}
