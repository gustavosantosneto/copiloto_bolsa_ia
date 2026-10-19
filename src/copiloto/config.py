"""Carrega config/parametros.toml + .env → Config validada."""

import os
import tomllib
from collections.abc import Mapping
from datetime import time
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, field_validator, model_validator

RAIZ = Path(__file__).resolve().parents[2]
TOML_PADRAO = RAIZ / "config" / "parametros.toml"
ENV_PADRAO = RAIZ / ".env"

TIMEFRAMES_MT5 = {
    "M1", "M2", "M3", "M4", "M5", "M6", "M10", "M12", "M15", "M20", "M30",
    "H1", "H2", "H3", "H4", "H6", "H8", "H12", "D1", "W1", "MN1",
}

Pct = Field(gt=0, le=100)


class ErroConfig(Exception):
    pass


class Secao(BaseModel):
    model_config = ConfigDict(extra="forbid")  # chave desconhecida = erro (pega typo)


class Geral(Secao):
    ambiente: Literal["demo", "real"]
    somente_leitura: bool
    fuso: str
    moeda: str


class Mt5(Secao):
    caminho_terminal: str = ""
    timeout_conexao_ms: int = Field(gt=0)
    tentativas_reconexao: int = Field(ge=0)
    intervalo_reconexao_s: float = Field(gt=0)


class Coletor(Secao):
    intervalo_poll_s: float = Field(gt=0)
    intervalo_poll_fora_pregao_s: float = Field(gt=0)
    intervalo_candles_s: float = Field(gt=0)
    historico_deals_dias: int = Field(gt=0)


class Pregao(Secao):
    abertura: time
    fechamento: time
    janela_operacao_inicio: time
    janela_operacao_fim: time

    @model_validator(mode="after")
    def _ordem(self):
        if not (self.abertura <= self.janela_operacao_inicio < self.janela_operacao_fim <= self.fechamento):
            raise ValueError("esperado abertura <= janela_inicio < janela_fim <= fechamento")
        return self


class Universo(Secao):
    watchlist: list[str] = Field(min_length=1)
    preco_max_acao: float = Field(gt=0)

    @field_validator("watchlist")
    @classmethod
    def _normaliza(cls, v: list[str]) -> list[str]:
        v = [t.strip().upper() for t in v]
        if len(set(v)) != len(v):
            raise ValueError("ticker duplicado")
        return v


class Timeframes(Secao):
    principal: str
    auxiliar: str
    disponiveis: list[str]

    @model_validator(mode="after")
    def _validos(self):
        invalidos = set(self.disponiveis) - TIMEFRAMES_MT5
        if invalidos:
            raise ValueError(f"timeframe inválido: {sorted(invalidos)}")
        if {self.principal, self.auxiliar} - set(self.disponiveis):
            raise ValueError("principal/auxiliar devem estar em disponiveis")
        return self


class Operacao(Secao):
    lote_padrao: int = Field(gt=0, multiple_of=100)
    corretagem: float = Field(ge=0)
    emolumentos_pct: float = Field(ge=0, le=100)
    max_operacoes_dia: int = Field(gt=0)
    ref_pct_nova_entrada: float = Field(gt=0, le=100)
    max_entradas_preco_medio: int = Field(gt=0)


class Risco(Secao):
    perda_max_dia: float = Pct
    perda_max_operacao: float = Field(gt=0)
    perda_aberta_max_ativo_pct: float = Pct
    perda_aberta_max_total_pct: float = Pct
    margem_usada_max_pct: float = Pct
    nivel_margem_min_pct: float = Field(gt=0)
    max_posicoes_abertas: int = Field(gt=0)
    alerta_correlacao_posicoes: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def _ativo_ate_total(self):
        if self.perda_aberta_max_ativo_pct > self.perda_aberta_max_total_pct:
            raise ValueError("perda_aberta_max_ativo_pct > perda_aberta_max_total_pct")
        return self


class Simulacao(Secao):
    capital_simulado: float = Field(ge=0)
    alavancagem_simulada: float = Field(ge=0)


class Registro(Secao):
    snapshot_antes_depois: bool
    comparar_margem_prevista: bool
    tolerancia_divergencia_margem_pct: float = Pct
    csv_historico: str
    csv_base_operacional: str
    min_medicoes_margem_validada: int = Field(gt=0)


class Persistencia(Secao):
    banco: str


class Similaridade(Secao):
    janela_sessoes: int = Field(gt=1)
    metodo_padrao: Literal["pearson", "xcorr", "dtw", "coint", "granger"]
    base: str
    limiar_direta: float = Field(gt=0, le=1)
    limiar_inversa: float = Field(ge=-1, lt=0)
    lag_max_candles: int = Field(ge=0)
    pct_fora_amostra: float = Field(gt=0, lt=100)


class Indicadores(Secao):
    ema_periodo: int = Field(gt=0)
    rsi_periodo: int = Field(gt=0)
    vwap: list[Literal["diaria", "semanal", "semana_anterior"]]


class Api(Secao):
    host: str
    porta: int = Field(gt=0, le=65535)


class Painel(Secao):
    refresh_s: float = Field(gt=0)
    tema: Literal["escuro", "claro"]
    casas_decimais: int = Field(ge=0, le=8)


class Alertas(Secao):
    simbolo_sem_cotacao_s: float = Field(gt=0)
    margem_zero_com_posicao: bool


class Log(Secao):
    nivel: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    pasta: str


class Credenciais(BaseModel):
    login: int | None = None
    senha: SecretStr | None = None
    servidor: str | None = None

    @property
    def completas(self) -> bool:
        return bool(self.login and self.senha and self.servidor)


class Config(Secao):
    geral: Geral
    mt5: Mt5
    coletor: Coletor
    pregao: Pregao
    universo: Universo
    timeframes: Timeframes
    operacao: Operacao
    risco: Risco
    simulacao: Simulacao
    registro: Registro
    persistencia: Persistencia
    similaridade: Similaridade
    indicadores: Indicadores
    api: Api
    painel: Painel
    alertas: Alertas
    log: Log
    credenciais: Credenciais = Credenciais()


def ler_credenciais(ambiente: str, fonte: Mapping[str, str | None]) -> Credenciais:
    """Lê MT5_{DEMO|REAL}_* da fonte; vazio vira None."""
    p = f"MT5_{ambiente.upper()}_"
    valores = {c: fonte.get(p + c.upper()) or None for c in ("login", "senha", "servidor")}
    try:
        return Credenciais.model_validate(valores)
    except ValidationError as e:
        raise ErroConfig(f".env {p}*: {_formata(e)}") from e


def carregar_config(caminho_toml: Path = TOML_PADRAO, caminho_env: Path = ENV_PADRAO) -> Config:
    try:
        with open(caminho_toml, "rb") as f:
            dados = tomllib.load(f)
    except FileNotFoundError as e:
        raise ErroConfig(f"config não encontrada: {caminho_toml}") from e
    except tomllib.TOMLDecodeError as e:
        raise ErroConfig(f"{caminho_toml.name}: TOML inválido — {e}") from e

    try:
        cfg = Config(**dados)
    except ValidationError as e:
        raise ErroConfig(f"{caminho_toml.name}:\n{_formata(e)}") from e

    fonte = {**dotenv_values(caminho_env), **os.environ}  # variável de ambiente sobrepõe .env
    cfg.credenciais = ler_credenciais(cfg.geral.ambiente, fonte)
    return cfg


def _formata(e: ValidationError) -> str:
    return "\n".join(f"  {'.'.join(map(str, err['loc'])) or '(raiz)'}: {err['msg']}" for err in e.errors())
