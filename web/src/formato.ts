// Formatação pt-BR. `casas` vem de [painel].casas_decimais.
let casas = 2;
export const definirCasas = (n: number) => (casas = n);

export const num = (v: number | null | undefined, c = casas) =>
  v == null ? "—" : v.toLocaleString("pt-BR", { minimumFractionDigits: c, maximumFractionDigits: c });
export const brl = (v: number | null | undefined) => (v == null ? "—" : `R$ ${num(v)}`);
export const inteiro = (v: number | null | undefined) => num(v, 0);
export const hora = (iso: string) => iso.slice(11, 19);
export const sinal = (v: number | null | undefined) => (v == null || v === 0 ? "" : v > 0 ? "pos" : "neg");
export const hoje = () => new Date().toLocaleDateString("sv"); // AAAA-MM-DD local
