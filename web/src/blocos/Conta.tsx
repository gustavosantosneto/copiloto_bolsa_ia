// Bloco 1 — Conta (MT5) + conta usada no cálculo (simulada na demo)
import { Card } from "../Card";
import type { Capacidade, Conta as TConta } from "../api";
import { brl, num, sinal } from "../formato";

function Item({ rotulo, valor, classe = "" }: { rotulo: string; valor: string; classe?: string }) {
  return (
    <div className="item">
      <span className="rotulo">{rotulo}</span>
      <span className={`valor ${classe}`}>{valor}</span>
    </div>
  );
}

export function Conta({ conta, cap }: { conta?: TConta; cap?: Capacidade }) {
  const c = cap?.conta;
  return (
    <Card id="conta" titulo={<>Conta</>}>
      {c && (
        <>
          <div className="sub">{cap.modo === "simulado" ? "Simulada (base dos cálculos)" : "Conta"}</div>
          <div className="grade">
            <Item rotulo="Saldo" valor={brl(c.saldo)} />
            <Item rotulo="Patrimônio" valor={brl(c.patrimonio)} />
            <Item rotulo="Margem usada" valor={brl(c.margem_usada)} />
            <Item rotulo="Margem livre" valor={brl(c.margem_livre)} />
            <Item rotulo="Valor em posições" valor={brl(c.valor_posicoes)} />
            <Item rotulo="Alavancagem efetiva" valor={c.alavancagem_efetiva == null ? "—" : `${num(c.alavancagem_efetiva)}x`} />
            <Item rotulo="Folga perda total" valor={brl(c.folga_perda_total)} classe={sinal(c.folga_perda_total)} />
          </div>
        </>
      )}
      {conta && (
        <>
          <div className="sub">MT5 {conta.modo} · {conta.corretora} · {conta.login}</div>
          <div className="grade">
            <Item rotulo="Saldo" valor={brl(conta.saldo)} />
            <Item rotulo="Patrimônio" valor={brl(conta.patrimonio)} />
            <Item rotulo="Margem" valor={brl(conta.margem)} />
            <Item rotulo="Margem livre" valor={brl(conta.margem_livre)} />
            <Item rotulo="Nível de margem" valor={conta.nivel_margem ? `${num(conta.nivel_margem, 0)}%` : "—"} />
            <Item rotulo="Lucro aberto" valor={brl(conta.lucro_aberto)} classe={sinal(conta.lucro_aberto)} />
          </div>
        </>
      )}
    </Card>
  );
}
