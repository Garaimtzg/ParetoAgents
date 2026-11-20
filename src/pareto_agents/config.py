"""Carga y valida la configuración congelada en la Fase 0."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
EFFORTS = {"low", "medium", "high", "xhigh", "max"}


@dataclass(frozen=True)
class Role:
    role: str
    model: str  # model ID completo, p. ej. claude-opus-5-5
    effort: str


@dataclass(frozen=True)
class Variant:
    id: str  # p. ej. "A1-SDK"
    topology: str
    track: str
    roles: tuple[Role, ...]
    subagents_enabled: bool


def load_yaml(rel_path: str | Path) -> dict:
    return yaml.safe_load((REPO_ROOT / rel_path).read_text())


def load_experiment() -> dict:
    return load_yaml("config/experiment.yaml")


def load_variants(path: str | Path = "config/variants.yaml") -> list[Variant]:
    data = load_yaml(path)
    aliases: dict[str, str] = data["models"]
    variants: list[Variant] = []
    for topo_id, topo in data["topologies"].items():
        roles = []
        for r in topo["roles"]:
            if r["effort"] not in EFFORTS:
                raise ValueError(f"{topo_id}/{r['role']}: effort inválido {r['effort']!r}")
            roles.append(Role(r["role"], aliases[r["model"]], r["effort"]))
        tracks = ["solo"] if topo.get("single_track") else data["tracks"]
        for track in tracks:
            variants.append(
                Variant(
                    id=topo_id if track == "solo" else f"{topo_id}-{track.upper()}",
                    topology=topo_id,
                    track=track,
                    roles=tuple(roles),
                    subagents_enabled=(track == "cc" and topo["cc"]["subagents_enabled"]),
                )
            )
    return variants
