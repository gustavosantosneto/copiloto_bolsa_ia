# copiloto_bolsa_ia

Copiloto de trading integrado ao MetaTrader 5 via Python.

- Leis: [CONSTITUICAO.md](docs/CONSTITUICAO.md)
- Regras: [OPERACIONAL.md](docs/OPERACIONAL.md)
- Painel: [PAINEL.md](docs/PAINEL.md)
- Fases: [ROADMAP.md](docs/ROADMAP.md)
- Contexto/histórico: [CONTEXTO.md](docs/CONTEXTO.md)
- Parâmetros: [config/parametros.toml](config/parametros.toml)
- Dados medidos: [dados/](dados/)
- Agente de código: [CLAUDE.md](CLAUDE.md)

## Rodar
- `pip install -e ".[dev]"` (Python 3.13, `.venv`) · Node 22+
- `.env` a partir de `.env.example` (login demo)
- `copiloto painel` → coletor + API + web → http://localhost:5173
- CLI: `copiloto --help` (`conta`, `posicoes`, `capacidade`, `alertas`, `registro`…)
