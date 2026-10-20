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
- Versões: **v1 em uso** = `D:\Github\mt5_copiloto_ia_v1` (branch `v1`, http://localhost:5180, inicia com o Windows) · **beta** = este repo (branch `beta`, http://localhost:5190, testes na demo) → `main` após validar
- `copiloto painel` → coletor + API + web (portas em `[api]`/`[painel]`)
- Terminal fora do VS Code (PowerShell/cmd): `D:\Github\mt5_copiloto_ia_v1\.venv\Scripts\copiloto.exe painel` (v1)
- Inicia com o Windows: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\copiloto_painel.cmd` (apagar o arquivo desliga)
- CLI: `copiloto --help` → `config`, `conta`, `posicoes`, `ordens`, `historico`, `simbolos`, `capacidade`, `atencoes`, `spread`, `mercado`, `registro`, `base`, `resultado`, `corretoras`, `coletar`, `api`, `painel`
