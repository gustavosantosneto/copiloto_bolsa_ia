# Painel — copiloto_bolsa_ia

> O que o painel web mostra. Subordinado à [CONSTITUICAO.md](CONSTITUICAO.md); cálculos em [OPERACIONAL.md](OPERACIONAL.md).
> Diretriz: claro, rápido, barato, simples. Funciona **sem o agente**. Coluna "Fase" = [ROADMAP.md](ROADMAP.md).
> Layout: cards de mesmo tamanho em colunas que preenchem a tela sem rolagem (rolagem só dentro do card); recolher → 1 linha, os outros crescem. Atenções (bloco 7) = lateral direita ≤20%, histórico agrupado por tipo+ativo, mais nova em cima.

| # | Bloco | Conteúdo | Fase |
|---|---|---|---|
| 1 | Conta | Saldo, patrimônio, margem usada/livre, nível de margem, alavancagem efetiva | V1 |
| 2 | Posições e ordens | Abertas, pendentes, preço médio, SL, TP, P&L aberto | V1 |
| 3 | Capacidade operacional | Lotes padrão operáveis por ativo (saldo, margem livre, margem medida, qtd em carteira) · spread atual e z (V1.1) | V1 |
| 4 | Histórico | Deals do dia/período + snapshot antes/depois | V1 |
| 5 | Base operacional | Margem medida × alavancagem declarada, custos medidos, nº medições | V1.1 |
| 6 | Resultado | Bruto/líquido, custo médio, ganho médio por operação e dia, drawdown · modo Diagnóstico: MAE/MFE por operação, por motivo de saída (beta) | V1.1 |
| 7 | Atenções | Guardas: símbolo sem cotação, margem zero com posição (V1) · limites de risco, divergência de margem, spread (V1.1) | V1 · V1.1 |
| 8 | Similaridade | Matriz direta/inversa, lag, retornos normalizados comparados | V2 |
| 9 | Simulação | Nova entrada → impacto em margem, exposição, preço médio, TP | V2 |
| 10 | Chat agente | Pergunta livre → análise reproduzível | V4 |
| 11 | Confirmação | Confirmação explícita antes de qualquer ordem | V5 |
