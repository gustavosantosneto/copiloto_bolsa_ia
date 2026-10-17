# Constituição do Projeto — Auxiliador de Trading com IA

> Documento norteador. Toda decisão de produto, arquitetura ou código deve ser coerente com esta constituição. Alterações aqui exigem aprovação explícita do responsável pelo projeto.

## 1. Visão e propósito
Desenvolver um copiloto inteligente de trading, integrado ao MetaTrader 5 por Python, capaz de analisar mercados, investigar hipóteses, gerenciar riscos e patrimônio, acompanhar operações e auxiliar decisões em tempo quase real.

**Princípio fundamental:** a IA deve funcionar como analista, pesquisadora e copiloto, não apenas como executora de scripts ou robô autônomo.

## 2. Integração MT5 + Python
- Utilizar o SDK oficial `MetaTrader5`.
- Obter candles históricos, ticks, cotações, posições, ordens e informações da conta.
- Trabalhar inicialmente com aproximadamente 17 ações brasileiras.
- Timeframe principal M12, com M6 auxiliar e possibilidade de outros períodos.
- Permitir alternância entre ambientes de demonstração e real.
- Centralizar a comunicação com MT5 em serviços reutilizáveis.

## 3. Similaridade e relações entre ativos
- Construir matrizes de correlação e similaridade entre ações.
- Identificar movimentos sincronizados, divergentes e defasados.
- Investigar ativos líderes e seguidores.
- Comparar retornos percentuais e padrões normalizados, não somente preços.
- Testar Pearson, correlação cruzada, DTW, cointegração e causalidade de Granger.
- Permitir janelas temporais, indicadores e limites configuráveis.
- Avaliar robustez estatística e desempenho fora da amostra.
- Investigar oportunidades de antecipação, convergência e reversão à média.

## 4. Gestão patrimonial e riscos
- Monitorar saldo, patrimônio, margem utilizada, margem livre e alavancagem.
- Consolidar exposição por ativo, direção e carteira.
- Acompanhar preço médio, lucro/prejuízo realizado e não realizado.
- Calcular drawdown, risco agregado e cenários de perda.
- Simular entradas adicionais e seus impactos sobre a margem.
- Considerar diferenças de margem exigida entre ativos e corretoras.
- Implementar limites configuráveis de risco por operação e por dia.
- Evitar concentração excessiva e considerar correlação entre posições.

## 5. Gestão de operações abertas
- Visualizar posições, ordens pendentes, preços médios, SL e TP.
- Identificar possíveis ajustes de take profit e stop loss.
- Simular novas entradas e estratégias de preço médio.
- Sugerir encerramentos parciais ou totais.
- Oferecer funções como `get_margin`, `set_take_profit`, `add_position` e `cancel_order`.
- Exigir confirmação humana explícita antes de qualquer execução financeira.
- Manter registros auditáveis das sugestões, decisões e ações.

## 6. Análise técnica e avaliação de estratégias
- Implementar VWAP diária, semanal e da semana anterior.
- Calcular EMA24, RSI(10) e indicadores adicionais.
- Investigar gap fill, mean reversion, dojis e comportamento da abertura.
- Desenvolver mecanismos de backtesting e simulação.
- Medir MAE, MFE, profit factor, drawdown e expectativa matemática.
- Catalogar operações, padrões, hipóteses e resultados.
- Considerar custos operacionais, slippage e vieses estatísticos.

## 7. Agente inteligente e investigação
- Permitir perguntas abertas em linguagem natural.
- Traduzir hipóteses em experimentos quantitativos.
- Selecionar bibliotecas e metodologias adequadas.
- Executar análises e comparar alternativas.
- Explicar resultados, incertezas e limitações.
- Diferenciar correlação, causalidade e coincidência estatística.
- Explorar LangGraph, MCP, RD-Agent(Q), FinRobot e modelos especializados.
- Priorizar componentes existentes e soluções reutilizáveis, evitando reinventar ferramentas consolidadas.

**Objetivo:** conseguir perguntar algo como *"Quais ações anteciparam os movimentos de ITUB4 nas últimas 100 sessões, com consistência estatística?"* e receber uma investigação fundamentada, não apenas código para executar manualmente.

## 8. Interface e experiência
- Desenvolver painel web/HTML para visualizar mercado e carteira.
- Apresentar posições abertas, patrimônio, exposição e alertas.
- Disponibilizar matrizes de similaridade e gráficos comparativos.
- Oferecer chat para interação com o agente.
- Permitir simulações e confirmações de operações.
- Priorizar clareza, velocidade, baixo custo e simplicidade operacional.

## 9. Arquitetura
| Camada | Responsabilidade |
|---|---|
| **Dados** | MT5 SDK e armazenamento histórico local |
| **Backend** | Python modular, APIs e serviços especializados |
| **Análise quantitativa** | Bibliotecas estatísticas e financeiras |
| **Agente** | LLM com ferramentas, memória operacional e acesso controlado aos serviços |
| **Interface** | Aplicação web para monitoramento e interação |
| **Persistência** | Banco de dados para histórico, operações, testes e decisões |
| **Segurança** | Isolamento entre análise, simulação e execução real |

## 10. Princípios de desenvolvimento
1. Construir incrementalmente, com funcionalidades pequenas e verificáveis.
2. Priorizar precisão dos dados, transparência e rastreabilidade.
3. Reutilizar bibliotecas maduras antes de criar implementações próprias.
4. Separar claramente dados, análises, decisões e execução.
5. Nunca executar ordens reais sem autorização humana explícita.
6. Não confundir resultados históricos com capacidade preditiva comprovada.
7. Validar hipóteses fora da amostra antes de utilizá-las operacionalmente.
8. Manter componentes desacoplados, testáveis e extensíveis.
9. Evitar complexidade prematura e dependência desnecessária de serviços pagos.
10. Preservar o controle humano sobre capital, risco e decisões.

## 11. Evolução por fases

| Fase | Nome | Escopo |
|---|---|---|
| 1 | **Fundação** | Integração MT5, consulta de dados históricos e da conta, estrutura Python e persistência |
| 2 | **Patrimônio e operações** | Monitoramento de posições, exposição, margem, P&L e simulação de novas entradas |
| 3 | **Inteligência quantitativa** | Indicadores, similaridade entre ativos, relações temporais, backtests e validação de hipóteses |
| 4 | **Agente IA** | Chat integrado às ferramentas Python e MT5, investigação autônoma de hipóteses e explicação de resultados |
| 5 | **Copiloto operacional** | Painel completo, alertas contextuais, sugestões de gestão e execução supervisionada |

## 12. Critério de sucesso
O projeto será considerado funcional quando permitir:

- Consultar o estado da conta e das operações em tempo quase real.
- Investigar relações entre ações utilizando dados históricos.
- Simular decisões e seus impactos sobre risco e patrimônio.
- Fazer perguntas livres e receber análises quantitativas reproduzíveis.
- Receber sugestões contextualizadas sem perder o controle das decisões.
- Registrar resultados e evoluir continuamente as metodologias.

---

**Diretriz final:** construir uma inteligência que amplie minha capacidade de investigar, compreender e decidir no mercado financeiro, com disciplina, autonomia intelectual e preservação de capital.
