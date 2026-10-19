# Roadmap — copiloto_bolsa_ia

> Gestão de produto (PO). Operar cedo, evoluir operando. Cada fase entrega algo usável. Fase só começa com a anterior em uso real.

## Arquitetura V1
```
MT5 terminal ──IPC──> coletor Python (poll 1s) ──> CSV (SQLite quando crescer)
                                                    ├─> API (somente leitura) ──> Web (painel)
                                                    └─> CLI (humano e Claude rodam comandos)
```
- Web não depende do agente. Agente usa a mesma CLI/API.
- V1 = **somente leitura**. Nenhuma ordem enviada pelo sistema.

## Fases
| Fase | Nome | Entrega | Pronto quando |
|---|---|---|---|
| **V1** | Olhar | Coletor MT5, registro de deals + snapshot antes/depois, capacidade por ativo, painel leitura, CLI | Opero no MT5 e vejo conta/posições/histórico no painel em ~1s |
| V1.1 | Medir | Margem/alavancagem/custos medidos por ativo, P&L líquido, stats por dia, alertas de limite | `base_operacional` preenchida pelos trades reais |
| V2 | Relacionar | Similaridade direta/inversa, lag líder→seguidor, simulação de nova entrada/preço médio | Matriz no painel com robustez fora da amostra |
| V3 | Testar | Indicadores (VWAP, EMA24, RSI10), backtest com custos, MAE/MFE, catálogo de hipóteses | Hipótese testada com relatório reproduzível |
| V4 | Investigar | Chat agente no painel usando ferramentas da CLI | Pergunta livre → análise com limites declarados |
| V5 | Copilotar | Sugestões de gestão, execução supervisionada com confirmação, auditoria | Ordem só sai após confirmação explícita registrada |

## Backlog V1
- [x] Estrutura Python + `config/parametros.toml` + `.env` (login MT5) — 2026-10-19
- [x] Serviço MT5: conectar, conta, posições, ordens, deals, símbolos — 2026-10-19
- [x] Coletor: poll 1s, diff de tickets → evento de deal — 2026-10-19 (validado ao vivo: RADL3 TP detectado em 122 ms)
- [x] Registro: deal + snapshot antes/depois → CSV `dados/historico_trades.csv` (append imediato + import do histórico MT5) — 2026-10-19
- [ ] SQLite: só quando o histórico crescer (decidido 2026-10-19); CSV por enquanto
- [x] Capacidade operacional por ativo da watchlist — 2026-10-19 (demo simulada R$5k × 200x; limites de exposição em revisão)
- [ ] Guardas: símbolo sem cotação, margem zero com posição (ver [CONTEXTO.md](CONTEXTO.md))
- [x] CLI: `conta`, `posicoes`, `ordens`, `historico`, `capacidade` + `simbolos`, `coletar` — 2026-10-19
- [ ] API leitura: mesmos recursos da CLI
- [ ] Web: blocos V1 do [PAINEL.md](PAINEL.md), refresh automático

## Backlog V1.1 (corretoras/custos — pesquisa 2026-10)
- [ ] Cadastro de corretoras e custos (day trade × swing, taxas B3, isenções)
- [ ] Matriz margem ativo × corretora × plataforma, com origem e `valido_ate`
- [ ] Custo efetivo por operação
- [ ] Simulação de capacidade de compra/alavancagem por corretora
- [ ] Comparativo de corretoras considerando integração MT5/API

## Fora da V1
Similaridade, indicadores, backtest, chat, execução de ordens, EA MQL5, multi-conta.

## Decisões pendentes
| # | Decisão | Status |
|---|---|---|
| 1 | Stack web | **React** (painel crescerá) — decidido 2026-10-19 |
| 2 | Banco | **SQLite** local — decidido 2026-10-19; adiado até histórico crescer, CSV na V1 |
| 3 | Formato config | **TOML** (`tomllib`) — decidido 2026-10-19 |
| 4 | Limites de risco | Decidido 2026-10-19: `perda_max_dia` % do saldo início do dia; exposição (valor posição) e margem usada = limites separados |
| 5 | Corretora alvo real | pendente |
| 6 | Evento instantâneo | Polling 1s na V1; EA `OnTradeTransaction` só se necessário |
