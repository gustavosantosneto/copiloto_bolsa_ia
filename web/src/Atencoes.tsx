// Atenções (apoio, nunca decisivo) — lateral direita com histórico. Repetidas agrupam (tipo + ativo): mostra só a última.
// Ordem: ocorrência mais nova em cima. Some e volta em < 2 min = mesma ocorrência. Histórico fica no navegador (localStorage), só conveniência.
import { useEffect, useState } from "react";
import type { Atencao } from "./api";

type Item = { a: Atencao; inicio: string; ultima: string; vezes: number; ativa: boolean };
const CHAVE = "copiloto.atencoes";
const MAX = 200;
const RETORNO_MS = 120_000; // some e volta em até 2 min = mesma ocorrência (evita contar oscilação)

const chaveDe = (a: Atencao) => `${a.tipo}|${a.ticker ?? a.tickers?.join(",") ?? ""}`;
const hhmmss = (iso: string) => new Date(iso).toLocaleTimeString("pt-BR");

function carregar(): Record<string, Item> {
  try {
    return JSON.parse(localStorage.getItem(CHAVE) ?? "{}");
  } catch {
    return {};
  }
}

export function Atencoes({ atuais, atualizado }: { atuais?: Atencao[]; atualizado?: Date }) {
  const [hist, setHist] = useState<Record<string, Item>>(carregar);

  useEffect(() => {
    if (!atuais || !atualizado) return;
    const agora = atualizado.toISOString();
    setHist((h) => {
      const novo: Record<string, Item> = {};
      for (const [k, it] of Object.entries(h)) novo[k] = { ...it, ativa: false };
      for (const a of atuais) {
        const k = chaveDe(a), it = h[k];
        const continua = it && (it.ativa || Date.parse(agora) - Date.parse(it.ultima) < RETORNO_MS);
        novo[k] = continua
          ? { ...it, a, ultima: agora, ativa: true }
          : { a, inicio: agora, ultima: agora, vezes: (it?.vezes ?? 0) + 1, ativa: true };
      }
      const mantidos = Object.entries(novo).sort((x, y) => y[1].inicio.localeCompare(x[1].inicio)).slice(0, MAX);
      const r = Object.fromEntries(mantidos);
      try {
        localStorage.setItem(CHAVE, JSON.stringify(r));
      } catch {
        /* sem storage: histórico só nesta aba */
      }
      return r;
    });
  }, [atuais, atualizado]);

  const lista = Object.values(hist).sort((x, y) => y.inicio.localeCompare(x.inicio));
  const ativas = lista.filter((i) => i.ativa).length;
  return (
    <aside className="lateral">
      <div className="cabecalho">
        <h2>Atenções <span className="sub">{ativas} ativas</span></h2>
        <button className="recolher" onClick={() => setHist({})} title="limpar histórico">✕</button>
      </div>
      <div className="sub">apoio, nunca decisivo</div>
      <ul className="lista-atencoes">
        {lista.map((i) => (
          <li key={chaveDe(i.a)} className={i.ativa ? "ativa" : ""}>
            <div className="linha-topo">
              <b>{i.a.ticker ?? i.a.tickers?.join(", ") ?? i.a.tipo.replaceAll("_", " ")}</b>
              <span className="sub">{hhmmss(i.inicio)}{i.vezes > 1 ? ` · ${i.vezes}×` : ""}</span>
            </div>
            <div>{i.a.msg}</div>
            {!i.ativa && <div className="sub">encerrou {hhmmss(i.ultima)}</div>}
          </li>
        ))}
        {!lista.length && <li className="vazio">Nenhuma atenção</li>}
      </ul>
    </aside>
  );
}
