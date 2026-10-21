// Bloco 6 — Resultado realizado (bruto/líquido, custos, médias, drawdown) · modo Diagnóstico (MAE/MFE por operação)
import { useState } from "react";
import { Card } from "../Card";
import type { Resultado as TRes } from "../api";
import { brl, sinal } from "../formato";
import { Diagnostico } from "./Diagnostico";

export function Resultado({ res }: { res?: TRes }) {
  const t = res?.total;
  const [modo, setModo] = useState<"resultado" | "diagnostico">("resultado");
  const abas = (
    <div className="abas">
      <button className={modo === "resultado" ? "ativa" : ""} onClick={() => setModo("resultado")}>Resultado</button>
      <button className={modo === "diagnostico" ? "ativa" : ""} onClick={() => setModo("diagnostico")}>Diagnóstico</button>
    </div>
  );
  if (modo === "diagnostico")
    return (
      <Card id="resultado" acoes={abas} titulo={<>Diagnóstico <span className="sub">MAE/MFE por operação</span></>}>
        <Diagnostico />
      </Card>
    );
  return (
    <Card id="resultado" acoes={abas} titulo={<>Resultado realizado <span className="sub">{t ? `30 dias (${t.dias} com operação) · custos B3 estimados quando MT5 não lança` : ""}</span></>}>
      {t && (
        <div className="grade">
          <div className="item"><span className="rotulo">Líquido</span><span className={`valor ${sinal(t.liquido)}`}>{brl(t.liquido)}</span></div>
          <div className="item"><span className="rotulo">Bruto</span><span className="valor">{brl(t.bruto)}</span></div>
          <div className="item"><span className="rotulo">Custos</span><span className="valor">{brl(t.custos)}</span></div>
          <div className="item"><span className="rotulo">Ganho médio/operação</span><span className="valor">{brl(t.ganho_medio_operacao)}</span></div>
          <div className="item"><span className="rotulo">Ganho médio/dia</span><span className="valor">{brl(t.ganho_medio_dia)}</span></div>
          <div className="item"><span className="rotulo">Drawdown máx · atual</span><span className="valor neg">{brl(t.drawdown_max)} · {brl(t.drawdown_atual)}</span></div>
        </div>
      )}
      <table>
        <thead>
          <tr><th>Dia</th><th>Operações</th><th>Bruto</th><th>Custos</th><th>Líquido</th><th>Médio/op.</th><th>Custo/op.</th></tr>
        </thead>
        <tbody>
          {res?.por_dia.map((d) => (
            <tr key={d.dia}>
              <td>{d.dia}</td>
              <td>{d.operacoes}</td>
              <td>{brl(d.bruto)}</td>
              <td>{brl(d.custos)}</td>
              <td className={sinal(d.liquido)}>{brl(d.liquido)}</td>
              <td>{brl(d.ganho_medio_operacao)}</td>
              <td>{brl(d.custo_medio_operacao)}</td>
            </tr>
          ))}
          {!res?.por_dia.length && <tr><td colSpan={7} className="vazio">Sem deals no período</td></tr>}
        </tbody>
      </table>
    </Card>
  );
}
