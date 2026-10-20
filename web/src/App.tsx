// Painel V1 (somente leitura) — blocos de docs/PAINEL.md. Funciona sem o agente.
import { useEffect, useState } from "react";
import { usePoll, type Alerta, type Capacidade as TCap, type Config, type Conta as TConta, type Deal, type Ordem, type Posicao } from "./api";
import { Capacidade } from "./blocos/Capacidade";
import { Conta } from "./blocos/Conta";
import { Historico } from "./blocos/Historico";
import { Posicoes } from "./blocos/Posicoes";
import { definirCasas } from "./formato";

function Painel({ cfg }: { cfg: Config }) {
  const ms = cfg.painel.refresh_s * 1000;
  const conta = usePoll<TConta>("/conta", ms);
  const posicoes = usePoll<Posicao[]>("/posicoes", ms);
  const ordens = usePoll<Ordem[]>("/ordens", ms);
  const cap = usePoll<TCap>("/capacidade", ms);
  const alertas = usePoll<Alerta[]>("/alertas", ms);
  const deals = usePoll<Deal[]>("/registro?dias=1", ms);
  const erro = [conta, posicoes, ordens, cap, alertas, deals].find((e) => e.erro)?.erro;

  return (
    <>
      <header>
        <h1>Copiloto Bolsa</h1>
        <span className={`selo ${cfg.geral.ambiente}`}>{cfg.geral.ambiente.toUpperCase()}</span>
        {cfg.geral.somente_leitura && <span className="selo">somente leitura</span>}
        <span className="relogio">{erro ? <span className="neg">⚠ {erro}</span> : conta.atualizado?.toLocaleTimeString("pt-BR")}</span>
      </header>
      {!!alertas.dados?.length && (
        <section className="alertas">
          {alertas.dados.map((a, i) => (
            <div key={i}>⚠ <b>{a.ticker ?? a.tickers?.join(", ")}</b> — {a.msg}</div>
          ))}
        </section>
      )}
      <main>
        <Conta conta={conta.dados} cap={cap.dados} />
        <Posicoes posicoes={posicoes.dados} ordens={ordens.dados} />
        <Capacidade cap={cap.dados} />
        <Historico deals={deals.dados} />
      </main>
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
