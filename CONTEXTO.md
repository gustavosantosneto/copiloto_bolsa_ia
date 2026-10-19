# Contexto — fatos, preferências, histórico

> Conhecimento acumulado. **Não** é estado atual da conta nem sinal de operação. Dados de mercado aqui → fixtures de teste, nunca ordem.
> Formato: `item | valor | data | fonte | status`. Status: `observado` · `preferencia` · `hipotese` · `pendente`.

## Perfil
| Item | Valor | Data | Fonte | Status |
|---|---|---|---|---|
| Experiência | Estuda trading desde ~2019; usa MT5 | — | gpt_web | observado |
| Janela operação | 11h–16h, até ~4h/dia | — | gpt_web | preferencia |
| Operações/dia | ~6 | — | gpt_web | hipotese |
| Caixa real | ~R$5 mil → meta R$10 mil | — | gpt_web | observado |
| Meta aspiracional | R$100/dia com R$10 mil — **nunca** codificar como meta/garantia | — | gpt_web | preferencia |

## Universo
| Item | Valor | Data | Fonte | Status |
|---|---|---|---|---|
| Watchlist (17) | ABEV3, B3SA3, BBAS3, BBDC3, BBSE3, CXSE3, ENEV3, EQTL3, ITSA4, ITUB4, RADL3, RDOR3, RENT3, SANB11, SBSP3, TIMS3, VIVT3 | 2026-09-24 | terminal | observado |
| Timeframes gráficos | 16 em M12; SBSP3 em M2; M6 discutido | 2026-09-24 | terminal | observado |
| Universo pesquisa (27) | Large caps >R$40 bi. **≠ watchlist** | 2026-08-25 | gpt_web | observado |

## Indicadores do terminal
| Item | Valor | Data | Fonte | Status |
|---|---|---|---|---|
| VWAP | Full VWAP (Borela Tech), 2 instâncias: `g_period=0/1` (diária/semanal), `g_price=5/6`. Conferir código; lib Python pode não replicar | 2026-09-24 | terminal | pendente |
| Média | `period=24, method=1` (EMA) | 2026-09-24 | terminal | observado |
| RSI | custom `InpPeriodRSI=10` | 2026-09-24 | terminal | observado |
| Outros disponíveis | Volumes, MarketProfile, ZigZag, ATR, Bollinger. Disponível ≠ desejado | 2026-09-24 | terminal | observado |

## Margem e corretoras
| Item | Valor | Data | Fonte | Status |
|---|---|---|---|---|
| Planilha | `alavancagem_acoes_b3_2026.xlsx`: 27 ações × Clear, Rico, Genial, Toro, Modal | 2026-08-25 | gpt_web | observado |
| Clear | Máximos genéricos; ex. PETR4 125x | 2026-08-25 | site | observado |
| Genial | Faixas 25x/50x por ativo/plataforma | 2026-08-25 | site | observado |
| Rico/Toro/Modal | Sem matriz pública auditável | 2026-08-25 | site | observado |
| Pesquisa custos | 12 corretoras; corretagem zero/mínima; separar day trade × swing; taxas B3, plataforma, condições de isenção | 2026-10 | gpt_web | observado |
| XP | Até 200x, restrito por ativo | 2026-10 | site | observado |
| Clear | Até 200x em ações; PETR4 125x | 2026-10 | site | observado |
| Genial | 50x p/ 10 ativos; até 25x demais | 2026-10 | site | observado |
| Toro | Até 70x | 2026-10 | site | observado |
| Rico | Ex. público 10x, não universal | 2026-10 | site | observado |
| BTG | Na pesquisa; margem individual não confirmada | 2026-10 | site | pendente |
| Descoberta | Margem varia por ativo × corretora × plataforma × conta. Tabela pública = teto, não garantia | 2026-10 | gpt_web | observado |
| Regra | Valores reais só medidos na corretora escolhida; toda margem com origem e validade | — | — | regra |

## Trades históricos (fixtures)
→ [dados/historico_trades.csv](dados/historico_trades.csv). Casos de risco: RADL3 drawdown intradiário >R$400; BBAS3 fechado manual ~−R$623 (2026-09-24).

## Anomalias da XP Demo (testes de robustez)
| Caso | Dado | Data | Lição |
|---|---|---|---|
| Posição fantasma | Equity R$1.055.400,88, margin=0, 1 WDOG26 vendido @5.235, TP 5.213, sem SL, P&L +R$50 | 2026-09-24 | Posição + margem 0 ≠ risco nulo |
| Símbolo morto | WDOG26 fora do Market Watch, sem candles, preço congelado 5.230, sem histórico de deals | 2026-09-24 | Sem cotação viva → não sugerir nada |
| Margem irreal | Exposição ~R$99,5 mil (CPFE3, PETR4, RADL3) com margem ~R$431 | 2026-08-25 | Inconsistência; nunca extrapolar p/ real |

## Integração anterior
- Conector MCP antigo: `get_trading_account_info`, `get_trading_open_positions`, `get_trading_history_positions`, `get_trading_history_orders`, `get_marketwatch_symbols`, `get_chart_history`, `get_chart_ticks_history`, `list_open_charts`, `tester_run_backtest`, `tester_get_report`.
- Não são APIs do SDK `MetaTrader5`. Acordo era só leitura.
- Proposta não aprovada: `MQL5/Files/copilot_config.ini`.

## Perguntas-motivação
1. Quais ações se movem proporcionalmente juntas (ou inversas), com preços diferentes?
2. Quem antecipa quem, com que lag em candles?
3. Diferença atual entre similares = oportunidade? Funciona fora da amostra?
4. Como está a conta agora? Margem livre? Impacto de nova entrada?
5. Onde fica a próxima entrada; como muda preço médio e TP?
6. Conversar com investigador que faz o trabalho — sem eu escolher lib e escrever código.
