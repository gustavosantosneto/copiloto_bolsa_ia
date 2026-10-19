# Operacional — copiloto_bolsa_ia

> Regras de funcionamento. Subordinado à [CONSTITUICAO.md](CONSTITUICAO.md). Parâmetros: [config/parametros.toml](../config/parametros.toml). Fases: [ROADMAP.md](ROADMAP.md).

## 1. Integração MT5
- SDK oficial `MetaTrader5` (Python). Toda comunicação centralizada em um serviço.
- Lê: candles, ticks, cotações, posições, ordens, deals, conta.
- Universo: ações BR até ~R$50; watchlist em [CONTEXTO.md](CONTEXTO.md).
- Timeframe: M12 principal, M6 auxiliar; outros configuráveis.
- Ambiente demo/real alternável; demo padrão.
- Nomes do conector MCP antigo (`get_trading_*`, `tester_*`) ≠ API do SDK. Não depender deles.

## 2. Regras de operação
- Lote padrão: múltiplos de 100.
- Corretagem: zero.
- Emolumentos/taxas: medidos nas operações reais até calibrar.
- Margem: não confiar em alavancagem declarada (200x, 140x…). Medir por ativo.
- Quantidade operável/ativo = f(saldo, margem livre, margem medida, qtd em carteira).

## 3. Registro de estatísticas (regra de gestão)
Toda compra/venda, de qualquer ativo, **obrigatoriamente** registra:
- Snapshot conta **antes** e **depois** do deal: saldo, patrimônio, margem, margem livre, nível de margem.
- Deal: ticker, direção, qtd, preço, ticket, horário, custos cobrados.
- Derivados: `margem_por_lote = Δmargem / lotes`, `alavancagem_medida = valor_posicao / Δmargem`, custo real.
- Destino: [dados/historico_trades.csv](../dados/historico_trades.csv) (cada deal) → consolida [dados/base_operacional.csv](../dados/base_operacional.csv) (por ativo).
- Comparar sempre com o previsto pelo MT5 (`order_calc_margin`). Divergência → alerta.

## 4. Gestão patrimonial e risco
- Monitorar saldo, patrimônio, margem usada/livre, alavancagem efetiva.
- Exposição por ativo, direção, carteira. Preço médio, P&L realizado/aberto.
- Resultado bruto e líquido; custo médio e ganho médio por operação e por dia.
- Drawdown, risco agregado, cenários de perda.
- Limites de risco configuráveis (operação, dia, ativo).
- Máx. lotes por ativo (`max_lotes_ativo`), inclui os já em carteira.
- Perda aberta por ativo/total: limite = % do saldo; folga = limite + P&L aberto (entra em 0; −50 → folga 450). Folga ≤ 0 → 0 lotes novos.
- Evitar concentração; considerar correlação **direta e inversa** entre posições.
- Simular entrada adicional → impacto em margem e risco.

## 5. Operações abertas
- Ver posições, ordens pendentes, preço médio, SL, TP.
- Sugerir ajuste de SL/TP, preço médio, encerramento parcial/total.
- Funções alvo: `get_margin`, `set_take_profit`, `add_position`, `cancel_order`.
- Execução financeira só com confirmação humana explícita. Tudo auditado.
- Referência de nova entrada (hipótese): `ref_compra = ultima_compra * (1 - ref_pct/100)`; `ref_venda = ultima_venda * (1 + ref_pct/100)`. Última execução ≠ preço médio.

**Detecção de eventos (operações manuais no MT5):**
- SDK Python **não tem listener/callback**. Só consulta.
- V1: polling 1s (`positions_get`, `orders_get`, `history_deals_get`, `account_info`); detectar mudança por diff de tickets/volume. Custo baixo (IPC local).
- Futuro, se preciso: EA MQL5 com `OnTradeTransaction` → grava evento em arquivo/socket → Python consome. Evento instantâneo + snapshot exato do momento.
- Limitação do polling: snapshot "antes" = último poll (≤1s de defasagem). Aceitável p/ medir margem.

## 6. Similaridade entre ativos
- Matriz de correlação/similaridade sobre **retornos normalizados**, não preço.
- **Direta** (sobem juntas, ρ > 0) e **inversa** (uma sobe, outra desce, ρ < 0). Ambas destacadas.
- Sincronia, divergência, defasagem (líder → seguidor, lag em candles).
- Métodos: Pearson, correlação cruzada, DTW, cointegração, Granger.
- Janelas, limites, indicadores configuráveis.
- Robustez: fora da amostra, estabilidade por janela, tamanho da amostra.
- Usos: antecipação, convergência, reversão à média, hedge (pares inversos).

## 7. Análise técnica e estratégias
- VWAP diária, semanal, semana anterior; EMA24; RSI(10). Detalhe do terminal em [CONTEXTO.md](CONTEXTO.md).
- Estudar: gap fill, mean reversion, dojis, abertura.
- Backtest/simulação com custos e slippage.
- Métricas: MAE, MFE, profit factor, drawdown, expectativa.
- Catalogar operações, padrões, hipóteses, resultados.

## 8. Agente
- Pergunta livre → experimento quantitativo → resultado explicado (incerteza, limites).
- Escolhe biblioteca/método; usuário não escreve código por hipótese.
- Diferencia correlação, causalidade, coincidência.
- Candidatos: LangGraph, MCP, RD-Agent(Q), FinRobot.
- Ex.: *"Quais ações anteciparam ITUB4 nas últimas 100 sessões, com consistência?"*

## 9. Arquitetura
| Camada | Papel |
|---|---|
| Dados | SDK MT5 + histórico local |
| Core | Python modular: serviços MT5, cálculos, registro |
| Interfaces | CLI (comandos p/ humano e agente) + API (web) |
| Web | Painel de visualização, independente do agente ([PAINEL.md](PAINEL.md)) |
| Persistência | Banco local: snapshots, deals, decisões |
| Agente | LLM com ferramentas = mesmos comandos da CLI |
| Segurança | Análise / simulação / execução isoladas |

## 10. Princípios
1. Incremental, pequeno, verificável.
2. Precisão, transparência, rastreabilidade.
3. Biblioteca madura > implementação própria.
4. Desacoplado, testável, extensível.
5. Sem complexidade prematura nem serviço pago desnecessário.

## 11. Arquivos de conhecimento
| Arquivo | Conteúdo |
|---|---|
| [dados/base_operacional.csv](../dados/base_operacional.csv) | Margem, alavancagem, taxas medidas por ativo |
| [dados/historico_trades.csv](../dados/historico_trades.csv) | Todo deal + snapshot antes/depois |
| [CONTEXTO.md](CONTEXTO.md) | Fatos históricos, preferências, anomalias |
| [config/parametros.toml](../config/parametros.toml) | Parâmetros e defaults do sistema |
