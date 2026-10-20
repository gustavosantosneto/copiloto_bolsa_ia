# Operacional — copiloto_bolsa_ia

> Regras de funcionamento. Subordinado à [CONSTITUICAO.md](CONSTITUICAO.md). Parâmetros: [config/parametros.toml](../config/parametros.toml). Fases: [ROADMAP.md](ROADMAP.md).

## 1. Integração MT5
- SDK oficial `MetaTrader5` (Python). Toda comunicação centralizada em um serviço.
- Lê: candles, ticks, cotações, posições, ordens, deals, conta.
- Candles M1 + negócios tick a tick (preço, volume, lado agressor, bid/ask no instante) da watchlist p/ estudo → `data/mercado/` (fora do git; ticks em SQLite): 1ª carga 90 dias, depois incremental (`copiloto mercado`).
- Universo: ações BR até ~R$50; watchlist em [CONTEXTO.md](CONTEXTO.md).
- Timeframe: M12 principal, M6 auxiliar; outros configuráveis.
- Ambiente demo/real alternável; demo padrão.
- Nomes do conector MCP antigo (`get_trading_*`, `tester_*`) ≠ API do SDK. Não depender deles.

## 2. Regras de operação
- Lote padrão: múltiplos de 100.
- Corretagem: zero.
- Emolumentos/taxas: custo lançado pelo MT5 tem prioridade; senão estimativa B3 (% por lado, day trade × swing) em [parametros.toml](../config/parametros.toml). Calibrar com nota de corretagem.
- Margem: não confiar em alavancagem declarada (200x, 140x…). Medir por ativo.
- Quantidade operável/ativo = f(saldo, margem livre, margem medida, qtd em carteira).

## 3. Registro de estatísticas (regra de gestão)
Toda compra/venda, de qualquer ativo, **obrigatoriamente** registra:
- Snapshot conta **antes** e **depois** do deal: saldo, patrimônio, margem, margem livre, nível de margem.
- Deal: ticker, direção, qtd, preço, ticket, horário, custos cobrados.
- Derivados: `margem_por_lote = Δmargem / lotes`, `alavancagem_medida = valor_posicao / Δmargem`, custo real.
- Destino: `dados/{conta}_historico_trades.csv` (cada deal) → consolida `dados/{conta}_base_operacional.csv` (por ativo). 1 arquivo por conta MT5.
- Medição válida: deal do coletor sozinho no ciclo, Δmargem ≠ 0. `n_medicoes` < `min_medicoes_margem_validada` → `pendente`.
- Comparar sempre com o previsto pelo MT5 (`order_calc_margin`). Divergência → atenção.

## 4. Gestão patrimonial e risco
- **Atenção** (não "alerta"): não é decisiva, nunca deve ser — é apenas apoio. Decisão é humana ([CONSTITUICAO.md](CONSTITUICAO.md) #2).
- Monitorar saldo, patrimônio, margem usada/livre, alavancagem efetiva.
- Exposição por ativo, direção, carteira. Preço médio, P&L realizado/aberto.
- Resultado bruto e líquido; custo médio e ganho médio por operação e por dia.
- Drawdown, risco agregado, cenários de perda.
- Limites de risco configuráveis (operação, dia, ativo).
- Máx. lotes por ativo (`max_lotes_ativo`), inclui os já em carteira.
- Perda aberta por ativo/total: limite = % do saldo; folga = limite + P&L aberto (entra em 0; −50 → folga 450). Folga ≤ 0 → 0 lotes novos.
- Evitar concentração; considerar correlação **direta e inversa** entre posições.
- Simular entrada adicional → impacto em margem e risco.
- Spread: `spread_pct = (ask − bid) / meio × 100`. Atenção se > teto (`spread_max_pct`) ou > média do ativo + N ticks (`ticks_acima_media`; M1 das últimas sessões, amostra mínima). Em ticks: spread B3 é quantizado, desvio padrão dispara à toa. Só no pregão. Histórico de spread = trava de apoio, nunca sinal de entrada.

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
- Diagnóstico (`copiloto diagnostico`): MAE/MFE de cada operação encerrada = pior/melhor P&L aberto tick a tick (preço médio e volume do instante), + motivo da saída (TP/SL/manual, do MT5). Preço = último negócio, sem custos.
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
| Persistência | CSV na V1 (`dados/`); SQLite quando crescer ([ROADMAP.md](ROADMAP.md)): snapshots, deals, decisões |
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
| `dados/{conta}_base_operacional.csv` | Margem, alavancagem medidas por ativo (gerado) |
| `dados/{conta}_historico_trades.csv` | Todo deal + snapshot antes/depois |
| [dados/corretoras.csv](../dados/corretoras.csv) · [dados/margens_corretora.csv](../dados/margens_corretora.csv) | Cadastro público de corretoras / margem ativo × corretora (teto, com validade) |
| `data/mercado/M1_{ticker}.csv` · `data/mercado/ticks.sqlite` | Candles + spread; negócios tick a tick p/ estudo (fora do git; nunca sinal) |
| [CONTEXTO.md](CONTEXTO.md) | Fatos históricos, preferências, anomalias |
| [config/parametros.toml](../config/parametros.toml) | Parâmetros e defaults do sistema |
