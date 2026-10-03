from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnswerMode(StrEnum):
    EXTRACTIVE = "extractive"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    database_url: SecretStr | None = None
    database_connect_timeout: int = Field(default=5, ge=1, le=30)
    stub_signing_key: SecretStr | None = None
    answer_mode: AnswerMode = AnswerMode.EXTRACTIVE
    question_characters: int = Field(default=4000, ge=1, le=4000)
    http_body_bytes: int = Field(default=16384, ge=1, le=65536)
    evidence_bytes: int = Field(default=12288, ge=1, le=65536)
    prompt_bytes: int = Field(default=32768, ge=1, le=131072)
    context_chunks: int = Field(default=5, ge=1, le=20)
    output_units: int = Field(default=512, ge=1, le=16384)
    output_bytes: int = Field(default=16384, ge=1, le=65536)
    max_statements: int = Field(default=5, ge=1, le=5)
    statement_characters: int = Field(default=2048, ge=1, le=2048)
    provider_seconds: float = Field(default=10, gt=0, le=30, allow_inf_nan=False)
    cost_ceiling: Decimal = Field(default=Decimal("0.01"), ge=0, allow_inf_nan=False)
    generation_backend: Literal["fake", "responses"] = "fake"
    generation_base_url: str | None = Field(default=None, repr=False)
    generation_model: str | None = None
    generation_reported_model: str | None = None
    generation_key_env: str | None = Field(default=None, repr=False)
    generation_reasoning_effort: Literal["low", "medium", "high"] = "medium"
    generation_output_tokens: int = Field(default=2048, ge=1, le=4096)
    generation_seconds: float = Field(default=60, gt=0, le=120, allow_inf_nan=False)
    generation_cost_ceiling: Decimal = Field(
        default=Decimal("0.55"), ge=0, le=Decimal("0.65"), allow_inf_nan=False
    )
    generation_price_version: str | None = None
    generation_price_source: str | None = None
    generation_input_price: Decimal | None = Field(
        default=None, ge=0, allow_inf_nan=False
    )
    generation_cached_price: Decimal | None = Field(
        default=None, ge=0, allow_inf_nan=False
    )
    generation_write_price: Decimal | None = Field(
        default=None, ge=0, allow_inf_nan=False
    )
    generation_output_price: Decimal | None = Field(
        default=None, ge=0, allow_inf_nan=False
    )
