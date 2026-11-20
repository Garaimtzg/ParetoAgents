"""Copia de trabajo de un repositorio de SWE-bench en su `base_commit`.

Versión simple de la Fase 1: un clon git en un directorio temporal, sin contenedor.
El agente solo tiene herramientas de lectura/edición y unos pocos comandos git de solo
lectura (ver runner.py), así que no ejecuta código del repositorio en tu máquina.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

CACHE = Path.home() / ".cache" / "pareto-agents" / "repos"


def _git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def _has_commit(repo_dir: Path, commit: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=repo_dir, capture_output=True
    ).returncode == 0


def mirror(repo: str, base_commit: str, url: str | None = None) -> Path:
    """Clon espejo en caché. Se descarga una vez y se actualiza si le falta el commit."""
    url = url or f"https://github.com/{repo}.git"
    dest = CACHE / repo.replace("/", "__")
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        _git("clone", "--mirror", url, str(dest))
    if not _has_commit(dest, base_commit):
        _git("remote", "set-url", "origin", url, cwd=dest)
        _git("fetch", "--prune", "origin", cwd=dest)
    return dest


def prepare(repo: str, base_commit: str, url: str | None = None) -> Path:
    src = mirror(repo, base_commit, url)
    work = Path(tempfile.mkdtemp(prefix="pareto-ws-"))
    _git("clone", "--quiet", "--shared", str(src), str(work))
    _git("checkout", "--quiet", "--detach", base_commit, cwd=work)
    _git("config", "user.email", "pareto@localhost", cwd=work)
    _git("config", "user.name", "pareto", cwd=work)
    return work


def diff(work: Path) -> str:
    """Parche final del agente respecto al base_commit (incluye archivos nuevos)."""
    _git("add", "-A", cwd=work)
    return _git("diff", "--cached", "--binary", "HEAD", cwd=work)
