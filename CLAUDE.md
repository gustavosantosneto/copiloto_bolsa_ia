# CLAUDE.md — copiloto_bolsa_ia

## Norte do projeto

A constituição abaixo é a referência máxima do projeto. Leia-a antes de qualquer tarefa e mantenha toda decisão coerente com ela. Em caso de conflito entre um pedido e a constituição, aponte o conflito e pergunte antes de agir.

@CONSTITUICAO.md

---

## Diretrizes de comportamento

Diretrizes para reduzir erros comuns de LLMs em código. Priorizam cautela sobre velocidade; em tarefas triviais, use bom senso.

### 1. Pense antes de codar
**Não assuma. Não esconda dúvidas. Exponha trade-offs.**

- Declare explicitamente suas suposições antes de implementar.
- Se houver mais de uma interpretação, apresente-as em vez de escolher em silêncio.
- Se existir uma abordagem mais simples, diga. Discorde quando fizer sentido.
- Se algo não estiver claro, pare, diga o que está confuso e pergunte.
- Nunca assuma regra de negócio ou de trading como verdade sem confirmar.

### 2. Simplicidade primeiro
**O mínimo de código que resolve o problema. Nada especulativo.**

- Nada de funcionalidades além do que foi pedido.
- Nada de abstrações para uso único nem "flexibilidade" não solicitada.
- Nada de tratamento de erro para cenários impossíveis.
- Se escreveu 200 linhas e caberia em 50, reescreva.
- Prefira bibliotecas maduras a implementações próprias.

Teste: *um engenheiro sênior diria que está complicado demais?* Se sim, simplifique.

### 3. Mudanças cirúrgicas
**Toque apenas no necessário. Limpe só a sua própria bagunça.**

- Não "melhore" código, comentários ou formatação adjacentes.
- Não refatore o que não está quebrado.
- Siga o estilo existente, mesmo que você faria diferente.
- Código morto não relacionado: mencione, não apague.
- Remova apenas imports/variáveis/funções que **suas** mudanças tornaram órfãos.

Teste: toda linha alterada deve ser rastreável ao pedido do usuário.

### 4. Execução orientada a objetivos
**Defina critérios de sucesso verificáveis e itere até atingi-los.**

- "Adicionar validação" → escreva testes para entradas inválidas e faça passar.
- "Corrigir bug" → escreva um teste que reproduza o bug e faça passar.
- "Novo indicador" → valide contra valores de referência conhecidos.

Para tarefas com várias etapas, apresente um plano curto:
```
1. [Etapa] → verificar: [checagem]
2. [Etapa] → verificar: [checagem]
```

---

## Regras específicas deste projeto

### Segurança financeira (inegociável)
- **Nunca** executar, alterar ou cancelar ordens reais sem confirmação humana explícita naquele momento.
- Ambiente **demo** é o padrão; ambiente real só com escolha explícita.
- Manter separação clara entre análise, simulação e execução.
- Registrar de forma auditável sugestões, decisões e ações.
- Nunca commitar credenciais, logins ou senhas de conta MT5 (usar `.env`).

### Rigor quantitativo
- Trabalhar com retornos/padrões normalizados, não só preços.
- Validar fora da amostra; declarar tamanho da amostra, período e limitações.
- Diferenciar correlação, causalidade e coincidência; alertar sobre overfitting e look-ahead bias.
- Considerar custos, slippage e vieses em backtests.
- Resultado histórico não é capacidade preditiva comprovada.

### Código e convenções
- Python modular; comunicação com MT5 centralizada em serviços reutilizáveis.
- Campos de negócio em `snake_case` e em português (ex.: `preco_medio`, `margem_livre`).
- Comentários compactos.
- MVP leve e simples, mas evolutivo; evitar dependências pagas desnecessárias.
- Construir incrementalmente, respeitando as fases da constituição.

### Colaboração
- Não fazer nada além do que foi pedido sem antes perguntar.
- Fazer perguntas relevantes e alinhar antes de criar algo novo.
