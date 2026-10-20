// Leitura da API Python (somente GET). Poll encadeado: próxima chamada só após a anterior terminar.
import { useEffect, useState } from "react";

export type Estado<T> = { dados?: T; erro?: string; atualizado?: Date };

export function usePoll<T>(caminho: string, intervaloMs: number): Estado<T> {
  const [estado, setEstado] = useState<Estado<T>>({});
  useEffect(() => {
    let ativo = true;
    let timer: number;
    const ler = async () => {
      try {
        const r = await fetch(`/api${caminho}`);
        const corpo = await r.json();
        if (!r.ok) throw new Error(corpo.detail ?? r.statusText);
        if (ativo) setEstado({ dados: corpo as T, atualizado: new Date() });
      } catch (e) {
        if (ativo) setEstado((s) => ({ ...s, erro: String(e instanceof Error ? e.message : e) }));
      }
      if (ativo) timer = window.setTimeout(ler, intervaloMs);
    };
    ler();
    return () => {
      ativo = false;
      clearTimeout(timer);
    };
  }, [caminho, intervaloMs]);
  return estado;
}

export type Conta = {
  login: number; servidor: string; corretora: string; modo: string; saldo: number; patrimonio: number;
  margem: number; margem_livre: number; nivel_margem: number; lucro_aberto: number; alavancagem_declarada: number;
};
export type Posicao = {
  ticket: number; ticker: string; direcao: string; volume: number; preco_medio: number; preco_atual: number;
  sl: number; tp: number; lucro: number; abertura: string;
};
export type Ordem = {
  ticket: number; ticker: string; tipo: string; volume_atual: number; preco: number; sl: number; tp: number; colocada: string;
};
export type AtivoCapacidade = {
  ticker: string; preco: number | null; qtd_carteira: number; lucro_aberto: number; folga_perda_ativo: number;
  margem_lote?: number; alavancagem_lote?: number; lotes_por_limite?: Record<string, number>;
  lotes_operaveis: number; restricao: string;
};
export type Capacidade = {
  modo: string;
  conta: {
    saldo: number; patrimonio: number; margem_usada: number; margem_livre: number; valor_posicoes: number;
    alavancagem_efetiva: number | null; limite_perda_ativo: number; folga_perda_total: number;
  };
  ignoradas_fora_universo: string[];
  ativos: AtivoCapacidade[];
};
export type Spread = {
  ticker: string; spread_pct: number | null; spread_ticks: number | null; media_pct: number | null; media_ticks: number | null;
  acima_media_ticks: number | null;
  n_amostras: number; status: string;
};
export type Atencao = { tipo: string; ticker?: string; tickers?: string[]; msg: string };
export type Deal = {
  data_hora: string; ticker: string; tipo: string; entrada: string; qtd: number; preco: number; ticket_deal: number;
  resultado_liquido: number; margem_antes: number | null; margem_depois: number | null;
  margem_livre_antes: number | null; margem_livre_depois: number | null; margem_prevista_mt5: number | null;
  fonte: string;
};
export type BaseAtivo = {
  ticker: string; n_medicoes: number; margem_por_lote: number; alavancagem_medida: number; alavancagem_min: number;
  alavancagem_max: number; divergencia_mt5_max_pct: number | null; ultima_medicao: string; ambiente: string; status: string;
};
export type ResumoResultado = {
  deals: number; operacoes: number; bruto: number; custos: number; liquido: number;
  ganho_medio_operacao: number | null; custo_medio_operacao: number | null;
};
export type Resultado = {
  total: ResumoResultado & { dias: number; ganho_medio_dia: number | null; drawdown_max: number; drawdown_atual: number };
  por_dia: (ResumoResultado & { dia: string })[];
};
export type Config = {
  geral: { ambiente: string; somente_leitura: boolean };
  painel: { refresh_s: number; tema: string; casas_decimais: number };
};
