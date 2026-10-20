// Bloco 5 — Base operacional: margem/alavancagem medidas por ativo × alavancagem declarada da conta
import { Card } from "../Card";
import type { BaseAtivo } from "../api";
import { brl, num } from "../formato";

export function Base({ base, declarada }: { base?: BaseAtivo[]; declarada?: number }) {
  return (
    <Card id="base" titulo={<>Base operacional <span className="sub">declarada pela conta: {declarada ? `${declarada}x` : "—"}</span></>}>
      <table>
        <thead>
          <tr>
            <th>Ativo</th><th>Medições</th><th>Margem/lote</th><th>Alavancagem medida</th><th>Mín–máx</th>
            <th>Diverg. MT5</th><th>Última</th><th>Status</th>
          </tr>
        </thead>
        <tbody>
          {base?.map((b) => (
            <tr key={b.ticker}>
              <td>{b.ticker}</td>
              <td>{b.n_medicoes}</td>
              <td>{brl(b.margem_por_lote)}</td>
              <td className="forte">{num(b.alavancagem_medida, 1)}x</td>
              <td className="sub">{num(b.alavancagem_min, 0)}–{num(b.alavancagem_max, 0)}x</td>
              <td>{b.divergencia_mt5_max_pct == null ? "—" : `${num(b.divergencia_mt5_max_pct)}%`}</td>
              <td className="sub">{b.ultima_medicao.slice(0, 10)}</td>
              <td className="sub">{b.status} · {b.ambiente}</td>
            </tr>
          ))}
          {!base?.length && <tr><td colSpan={8} className="vazio">Sem medições (deal ao vivo com snapshot)</td></tr>}
        </tbody>
      </table>
    </Card>
  );
}
