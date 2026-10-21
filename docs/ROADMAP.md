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
| V1.1 | Medir | Margem/alavancagem/custos medidos por ativo, P&L líquido, stats por dia, atenções de limite | `base_operacional` preenchida pelos trades reais |
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
- [x] Capacidade operacional por ativo da watchlist — 2026-10-19 (demo simulada R$5k × 200x)
- [x] Guardas: símbolo sem cotação, margem zero com posição (ver [CONTEXTO.md](CONTEXTO.md)) — 2026-10-19 (`copiloto atencoes`, `/atencoes`; capacidade zera sem cotação viva)
- [x] CLI: `conta`, `posicoes`, `ordens`, `historico`, `capacidade` + `simbolos`, `coletar` — 2026-10-19
- [x] API leitura: mesmos recursos da CLI (FastAPI, `copiloto api`, GET only) — 2026-10-19
- [x] Web: blocos V1 do [PAINEL.md](PAINEL.md), refresh automático — 2026-10-19 (React+Vite, 1s, `copiloto painel`)

→ Backlog V1 entregue 2026-10-19 (exceto SQLite, adiado). V1.1 antecipada por decisão do responsável 2026-10-20.

## Backlog V1.1 — 2026-10-20
- [x] Arquivos por conta: `dados/{conta}_*.csv` (base p/ SQLite por conta depois)
- [x] Base operacional: margem/alavancagem medidas por ativo, comparadas c/ MT5 (`copiloto base`, `/base`)
- [x] P&L líquido, stats por dia, drawdown realizado (`copiloto resultado`, `/resultado`)
- [x] Atenções de limite: perda dia/operação, perda aberta ativo/total, margem usada, nível de margem, divergência de margem
- [x] Custos: emolumentos B3 day trade × swing ([parametros.toml](../config/parametros.toml)); custo MT5 tem prioridade
- [x] Cadastro de corretoras + matriz ativo × corretora com origem e `valido_ate` (`dados/corretoras.csv`, `dados/margens_corretora.csv`)
- [x] Custo efetivo por operação + capacidade simulada por corretora (`copiloto corretoras`, `/corretoras`)
- [x] Candles M1 90 dias da watchlist p/ estudo, incremental (`copiloto mercado`) — 2026-10-20
- [x] Spread: atual × média do ativo em ticks, teto; atenção, nunca decisivo (`copiloto spread`, `/spread`) — 2026-10-20
- [x] "Alerta" → "atenção" (CLI `atencoes`, `/atencoes`) — 2026-10-20
- [x] Negócios tick a tick 90 d em SQLite, incremental (`copiloto mercado`) — 2026-10-20 (beta)
- [x] Diagnóstico MAE/MFE por operação + motivo da saída no registro (`copiloto diagnostico`, `/diagnostico`) — 2026-10-20 (beta)
- [x] Similaridade: matriz bruta/sem mercado, fora da amostra, estabilidade, atraso M1, cointegração, Granger + página no painel — 2026-10-20 (beta)
- [x] Base de uso 90 dias · matriz ao vivo dos últimos 60 min (VWAP de cada minuto; bruta, sem mercado, correlação/razão ±12) · atenções de concentração e hedge (≥3 posições) — 2026-10-20 (beta)
- [ ] Isenções / taxas de plataforma por corretora (sem fonte pública auditável)
- [ ] Painel: bloco de corretoras (hoje só CLI/API)

## Versões
- `v1` = em uso (`D:\Github\mt5_copiloto_ia_v1`) · `beta` = desenvolvimento, testes na demo · `main` = após validar. Dados da conta (`dados/{conta}_*.csv`) fora do git; fonte real = v1.

## Fora da V1
Similaridade, indicadores, backtest, chat, execução de ordens, EA MQL5, multi-conta.

## Decisões pendentes
| # | Decisão | Status |
|---|---|---|
| 1 | Stack web | **React** (painel crescerá) — decidido 2026-10-19 |
| 2 | Banco | **SQLite** local — decidido 2026-10-19; ticks já em SQLite (2026-10-20); deals ainda CSV |
| 3 | Formato config | **TOML** (`tomllib`) — decidido 2026-10-19 |
| 4 | Limites de risco | Decidido 2026-10-19: `perda_max_dia` % do saldo início do dia; `perda_aberta_max_ativo/total_pct` = P&L aberto (% do saldo, folga = limite + P&L); margem usada = limite separado |
| 5 | Corretora alvo real | pendente |
| 6 | Evento instantâneo | Polling 1s na V1; EA `OnTradeTransaction` só se necessário |
