// Painel V1 (somente leitura) — blocos de docs/PAINEL.md. Funciona sem o agente.
import { useEffect, useRef, useState, type ReactNode } from "react";
import { usePoll, type Atencao, type BaseAtivo, type Capacidade as TCap, type Config, type Conta as TConta, type Deal, type Ordem, type Posicao, type Resultado as TRes, type Spread } from "./api";
import { Atencoes } from "./Atencoes";
import { Similaridade } from "./Similaridade";
import { Base } from "./blocos/Base";
import { Capacidade } from "./blocos/Capacidade";
import { Conta } from "./blocos/Conta";
import { Historico } from "./blocos/Historico";
import { Posicoes } from "./blocos/Posicoes";
import { Resultado } from "./blocos/Resultado";
import { definirCasas } from "./formato";

// Nº de colunas pela largura da área dos cards; cada coluna empilha cards que dividem a altura (flex)
function useColunas(): [React.RefObject<HTMLElement | null>, number] {
  const ref = useRef<HTMLElement>(null);
  const [n, setN] = useState(2);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new ResizeObserver(([e]) => setN(e.contentRect.width >= 1500 ? 3 : e.contentRect.width >= 760 ? 2 : 1));
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return [ref, n];
}

function Colunas({ n, children }: { n: number; children: ReactNode[] }) {
  const por = Math.ceil(children.length / n);
  return (
    <>
      {Array.from({ length: n }, (_, i) => (
        <div key={i} className="coluna">{children.slice(i * por, (i + 1) * por)}</div>
      ))}
    </>
  );
}

type Pagina = "operacao" | "similaridade";
const lerPagina = (): Pagina => {
  try {
    return localStorage.getItem("copiloto.pagina") === "similaridade" ? "similaridade" : "operacao";
  } catch {
    return "operacao";
  }
};

function Painel({ cfg }: { cfg: Config }) {
  const [refMain, colunas] = useColunas();
  const [pagina, setPaginaEstado] = useState<Pagina>(lerPagina);
  const setPagina = (p: Pagina) => {
    setPaginaEstado(p);
    try {
      localStorage.setItem("copiloto.pagina", p);
    } catch {
      /* sem storage */
    }
  };
  const ms = cfg.painel.refresh_s * 1000;
  const conta = usePoll<TConta>("/conta", ms);
  const posicoes = usePoll<Posicao[]>("/posicoes", ms);
  const ordens = usePoll<Ordem[]>("/ordens", ms);
  const cap = usePoll<TCap>("/capacidade", ms);
  const atencoes = usePoll<Atencao[]>("/atencoes", ms);
  const deals = usePoll<Deal[]>("/registro?dias=1", ms);
  const base = usePoll<BaseAtivo[]>("/base", ms);
  const res = usePoll<TRes>("/resultado?dias=30", ms);
  const spread = usePoll<Spread[]>("/spread", ms);
  const erro = [conta, posicoes, ordens, cap, atencoes, deals, base, res, spread].find((e) => e.erro)?.erro;

  return (
    <>
      <header>
        <h1>Copiloto Bolsa</h1>
        <span className={`selo ${cfg.geral.ambiente}`}>{cfg.geral.ambiente.toUpperCase()}</span>
        {cfg.geral.somente_leitura && <span className="selo">somente leitura</span>}
        <nav className="abas">
          <button className={pagina === "operacao" ? "ativa" : ""} onClick={() => setPagina("operacao")}>Operação</button>
          <button className={pagina === "similaridade" ? "ativa" : ""} onClick={() => setPagina("similaridade")}>Similaridade</button>
        </nav>
        <span className="relogio">{erro ? <span className="neg">⚠ {erro}</span> : conta.atualizado?.toLocaleTimeString("pt-BR")}</span>
      </header>
      {pagina === "similaridade" && <div className="area"><Similaridade /></div>}
      <div className="area" hidden={pagina !== "operacao"}>
        <main ref={refMain} className={colunas === 1 ? "uma-coluna" : ""}>
          <Colunas n={colunas}>
            {[
              // ordem por coluna → 2 colunas: [Conta | Posições] [Deals | Resultado] [Capacidade | Base]
              <Conta key="conta" conta={conta.dados} cap={cap.dados} />,
              <Historico key="historico" deals={deals.dados} />,
              <Capacidade key="capacidade" cap={cap.dados} spread={spread.dados} />,
              <Posicoes key="posicoes" posicoes={posicoes.dados} ordens={ordens.dados} />,
              <Resultado key="resultado" res={res.dados} />,
              <Base key="base" base={base.dados} declarada={conta.dados?.alavancagem_declarada} />,
            ]}
          </Colunas>
        </main>
        <Atencoes atuais={atencoes.dados} atualizado={atencoes.atualizado} />
      </div>
    </>
  );
}

export function App() {
  const [cfg, setCfg] = useState<Config>();
  const [erro, setErro] = useState<string>();
  useEffect(() => {
    fetch("/api/config")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.statusText))))
      .then((c: Config) => {
        definirCasas(c.painel.casas_decimais);
        document.documentElement.dataset.tema = c.painel.tema;
        setCfg(c);
      })
      .catch((e) => setErro(`API indisponível (${e.message}). Rode: copiloto painel`));
  }, []);
  if (erro) return <p className="neg centro">{erro}</p>;
  return cfg ? <Painel cfg={cfg} /> : <p className="centro">Carregando…</p>;
}
