"""Contrato de mensagens (Iteração 0). Versão do esquema obrigatória (openness)."""
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

SCHEMA_VERSIONS = {1}

# (origem, categoria) -> último nível do tópico: dsm/<ambiente>/<origem>/<categoria>/<identificador>
SUBTOPICOS = {
    ("app", "interacao"): "tela",
    ("app", "quiz"): "resposta",
    ("app", "presenca"): "evento",
    ("app", "sensor"): "dispositivo",
    ("totem", "sensor"): "contagem",
}
OBRIGATORIOS = {
    "interacao": {"tela"},
    "quiz": {"questao", "perfil"},
    "presenca": {"evento_id"},
    "sensor": set(),
}


class Evento(BaseModel):
    event_id: UUID
    session_id: str = Field(min_length=8, max_length=64)
    categoria: str
    origem: str
    ts: datetime
    schema_version: int
    payload: dict

    @field_validator("ts")
    @classmethod
    def _ts_com_fuso(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("ts deve conter fuso horário")
        return v.astimezone(timezone.utc)

    @field_validator("schema_version")
    @classmethod
    def _versao(cls, v: int) -> int:
        if v not in SCHEMA_VERSIONS:
            raise ValueError(f"schema_version {v} não suportada")
        return v

    @model_validator(mode="after")
    def _regras(self):
        if (self.origem, self.categoria) not in SUBTOPICOS:
            raise ValueError(f"combinação inválida: {self.origem}/{self.categoria}")
        faltando = OBRIGATORIOS[self.categoria] - self.payload.keys()
        if faltando:
            raise ValueError(f"payload sem campos: {sorted(faltando)}")
        if self.categoria == "sensor":
            if self.origem == "totem":
                c = self.payload.get("contagem")
                if not isinstance(c, int) or isinstance(c, bool) or c < 0:
                    raise ValueError("contagem deve ser inteiro >= 0")
            elif "tipo" not in self.payload or "valor" not in self.payload:
                raise ValueError("sensor do app exige tipo e valor")
        return self


def parse_message(raw) -> Evento:
    """Valida bytes/str JSON. Levanta ValueError (ValidationError é subclasse)."""
    if isinstance(raw, bytearray):
        raw = bytes(raw)
    try:
        return Evento.model_validate_json(raw)
    except TypeError as e:  # payload None etc.
        raise ValueError(str(e)) from e


def topic_for(ev: Evento, ambiente: str = "prod") -> str:
    return f"dsm/{ambiente}/{ev.origem}/{ev.categoria}/{SUBTOPICOS[(ev.origem, ev.categoria)]}"


def topic_ok(topic: str, ev: Evento) -> bool:
    p = topic.split("/")
    return len(p) == 5 and p[0] == "dsm" and p[2] == ev.origem and p[3] == ev.categoria
