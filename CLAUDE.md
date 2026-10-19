# CLAUDE.md — copiloto_bolsa_ia

## Norte
Constituição = lei máxima; demais docs subordinados. Conflito entre pedido e docs → apontar e perguntar.

@CONSTITUICAO.md
@OPERACIONAL.md
@PAINEL.md
@ROADMAP.md
@CONTEXTO.md

## Mapa de conhecimento
| Tipo | Onde | Formato |
|---|---|---|
| Leis | `CONSTITUICAO.md` | mandamentos curtos |
| Regras | `OPERACIONAL.md` | tópicos por tema |
| Tela | `PAINEL.md` | tabela bloco × fase |
| Fases/backlog | `ROADMAP.md` | tabela + checklist |
| Fatos/histórico | `CONTEXTO.md` | tabela `item \| valor \| data \| fonte \| status` |
| Parâmetros | `config/parametros.toml` | chave = default + `# [status]` |
| Dados medidos | `dados/*.csv` | 1 linha por registro, separador `;`, cabeçalho snake_case |

## Formato dos docs (obrigatório)
- Estilo telegráfico: tópicos, tabelas, setas. Sem prosa, sem repetir o que outro doc já diz → linkar.
- Regra em `.md`; valor em `config/`; dado medido em `dados/`. Não misturar.
- Todo fato/valor histórico: data (`AAAA-MM-DD`), fonte, status (`observado` · `preferencia` · `hipotese` · `pendente` · `fixture`).
- Dado histórico de mercado = fixture de teste, nunca sinal/ordem.
- Novo conhecimento → doc existente certo; doc novo só se não couber, e perguntar antes.

## Comportamento
1. **Pense antes.** Declarar suposições; várias interpretações → apresentar; dúvida → perguntar. Nunca assumir regra de negócio/trading.
2. **Simples.** Mínimo de código; nada especulativo; sem abstração de uso único; biblioteca madura > própria. Respeitar fase atual do `ROADMAP.md`.
3. **Cirúrgico.** Tocar só o pedido; seguir estilo existente; código morto alheio → mencionar, não apagar.
4. **Orientado a verificação.** Critério verificável por tarefa; plano curto `etapa → verificar`.

## Segurança financeira (inegociável)
- Nunca executar/alterar/cancelar ordem real sem confirmação explícita no momento.
- Demo padrão; real só por escolha explícita. V1 = somente leitura.
- Análise / simulação / execução separadas. Tudo auditável.
- Credenciais só em `.env`, nunca commitadas.

## Rigor quantitativo
- Retornos normalizados, não preço. Correlação direta **e** inversa.
- Fora da amostra; declarar amostra, período, limites.
- Correlação ≠ causalidade ≠ coincidência; alertar overfitting e look-ahead.
- Custos, slippage, vieses em todo backtest. Histórico ≠ previsão.

## Código
- Python modular; MT5 centralizado em um serviço. CLI e API expõem as mesmas funções.
- Campos de negócio `snake_case` em português (`preco_medio`, `margem_livre`).
- Comentários compactos. MVP leve, evolutivo, sem dependência paga desnecessária.

## Colaboração
- Nada além do pedido sem perguntar. Alinhar antes de criar algo novo.
