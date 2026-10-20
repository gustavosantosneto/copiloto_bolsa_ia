// Bloco 2 — Posições abertas e ordens pendentes
import { Card } from "../Card";
import type { Ordem, Posicao } from "../api";
import { brl, hoje, hora, inteiro, num, sinal } from "../formato";

const alvo = (v: number) => (v ? num(v) : "—");

export function Posicoes({ posicoes, ordens }: { posicoes?: Posicao[]; ordens?: Ordem[] }) {
  return (
    <Card id="posicoes" titulo={<>Posições ({posicoes?.length ?? 0}) e ordens ({ordens?.length ?? 0})</>}>
      <table>
        <thead>
          <tr>
            <th>Ativo</th><th>Lado</th><th>Qtd</th><th>Preço médio</th><th>Atual</th>
            <th>TP</th><th>SL</th><th>P&L</th><th>Desde</th>
          </tr>
        </thead>
        <tbody>
          {posicoes?.map((p) => (
            <tr key={p.ticket}>
              <td>{p.ticker}</td>
              <td className={p.direcao}>{p.direcao}</td>
              <td>{inteiro(p.volume)}</td>
              <td>{num(p.preco_medio, 4)}</td>
              <td>{num(p.preco_atual)}</td>
              <td>{alvo(p.tp)}</td>
              <td className={p.sl ? "" : "neg"}>{alvo(p.sl)}</td>
              <td className={sinal(p.lucro)}>{brl(p.lucro)}</td>
              <td>{p.abertura.startsWith(hoje()) ? hora(p.abertura) : p.abertura.slice(0, 10)}</td>
            </tr>
          ))}
          {ordens?.map((o) => (
            <tr key={o.ticket} className="ordem">
              <td>{o.ticker}</td><td>{o.tipo}</td><td>{inteiro(o.volume_atual)}</td><td>{num(o.preco)}</td>
              <td>pendente</td><td>{alvo(o.tp)}</td><td>{alvo(o.sl)}</td><td>—</td><td>{hora(o.colocada)}</td>
            </tr>
          ))}
          {!posicoes?.length && !ordens?.length && (
            <tr><td colSpan={9} className="vazio">Nenhuma posição ou ordem</td></tr>
          )}
        </tbody>
      </table>
    </Card>
  );
}
