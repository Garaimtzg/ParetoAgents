"""Cálculo de coste en USD a partir de los tokens de una llamada.

Es el único cálculo de coste del proyecto: lo usan los dos tracks (SDK y CC),
así el coste se calcula igual en ambos (definición §3.4).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

PRICE_FIELDS = ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output")


@dataclass(frozen=True)
class Usage:
    """Tokens de UNA llamada a la API (campos de `response.usage`)."""

    input_tokens: int = 0
    cache_creation_5m_tokens: int = 0
    cache_creation_1h_tokens: int = 0
    cache_read_tokens: int = 0
    output_tokens: int = 0

    @property
    def prompt_tokens(self) -> int:
        """Longitud del prompt según Anthropic: toda la entrada, caché incluida."""
        return (
            self.input_tokens
            + self.cache_creation_5m_tokens
            + self.cache_creation_1h_tokens
            + self.cache_read_tokens
        )


@dataclass(frozen=True)
class Tier:
    max_prompt_tokens: int | None
    input: float
    cache_write_5m: float
    cache_write_1h: float
    cache_read: float
    output: float


@dataclass(frozen=True)
class CostBreakdown:
    input: float
    cache_write: float
    cache_read: float
    output: float
    long_context_tier: bool

    @property
    def total(self) -> float:
        return self.input + self.cache_write + self.cache_read + self.output


class PriceTable:
    def __init__(self, models: dict[str, list[Tier]], retrieved: str):
        self.models = models
        self.retrieved = retrieved

    @classmethod
    def load(cls, path: str | Path) -> "PriceTable":
        data = yaml.safe_load(Path(path).read_text())
        models: dict[str, list[Tier]] = {}
        for model_id, spec in data["models"].items():
            tiers = [Tier(**t) for t in spec["tiers"]]
            if not tiers or tiers[-1].max_prompt_tokens is not None:
                raise ValueError(f"{model_id}: el último tramo debe ser abierto (null)")
            models[model_id] = tiers
        return cls(models, str(data["retrieved"]))

    def tier_for(self, model: str, usage: Usage) -> tuple[Tier, bool]:
        """Devuelve el tramo aplicable y si es un tramo de contexto largo (no el primero)."""
        tiers = self.models[model]
        for i, tier in enumerate(tiers):
            if tier.max_prompt_tokens is None or usage.prompt_tokens <= tier.max_prompt_tokens:
                return tier, i > 0
        raise AssertionError("unreachable: el último tramo es abierto")

    def cost(self, model: str, usage: Usage) -> CostBreakdown:
        tier, long_tier = self.tier_for(model, usage)
        m = 1_000_000
        return CostBreakdown(
            input=usage.input_tokens * tier.input / m,
            cache_write=(
                usage.cache_creation_5m_tokens * tier.cache_write_5m
                + usage.cache_creation_1h_tokens * tier.cache_write_1h
            )
            / m,
            cache_read=usage.cache_read_tokens * tier.cache_read / m,
            output=usage.output_tokens * tier.output / m,
            long_context_tier=long_tier,
        )
