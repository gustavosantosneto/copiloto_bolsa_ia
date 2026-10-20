// Card do painel: título + botão recolher/expandir. Recolhido = 1 linha; os demais da coluna crescem (flex).
import { useState, type ReactNode } from "react";

const chave = (id: string) => `copiloto.recolhido.${id}`;

function lerRecolhido(id: string): boolean {
  try {
    return localStorage.getItem(chave(id)) === "1";
  } catch {
    return false;
  }
}

export function Card({ id, titulo, children }: { id: string; titulo: ReactNode; children: ReactNode }) {
  const [recolhido, setRecolhido] = useState(() => lerRecolhido(id));
  const alternar = () => {
    setRecolhido(!recolhido);
    try {
      localStorage.setItem(chave(id), recolhido ? "0" : "1");
    } catch {
      /* sem storage: só não lembra */
    }
  };
  return (
    <section className={`bloco${recolhido ? " recolhido" : ""}`}>
      <div className="cabecalho">
        <h2>{titulo}</h2>
        <button className="recolher" onClick={alternar} title={recolhido ? "expandir" : "recolher"}>
          {recolhido ? "▸" : "▾"}
        </button>
      </div>
      {!recolhido && <div className="corpo">{children}</div>}
    </section>
  );
}
