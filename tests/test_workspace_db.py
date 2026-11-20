import subprocess

from pareto_agents import db, workspace


def _git(*a, cwd):
    subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)


def _make_origin(path, content):
    path.mkdir()
    _git("init", "-q", cwd=path)
    (path / "a.py").write_text(content)
    _git("add", ".", cwd=path)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base", cwd=path)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True).stdout.strip()


def test_stale_cache_is_refreshed(tmp_path, monkeypatch):
    # Mismo nombre de repo, origen distinto: el commit nuevo no está en la caché.
    monkeypatch.setattr(workspace, "CACHE", tmp_path / "cache")
    workspace.prepare("toy/repo", _make_origin(tmp_path / "o1", "x = 1\n"), url=str(tmp_path / "o1"))
    base2 = _make_origin(tmp_path / "o2", "x = 9\n")
    work = workspace.prepare("toy/repo", base2, url=str(tmp_path / "o2"))
    assert (work / "a.py").read_text() == "x = 9\n"


def test_prepare_and_diff(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, "CACHE", tmp_path / "cache")
    origin = tmp_path / "origin"
    base = _make_origin(origin, "x = 1\n")

    work = workspace.prepare("toy/repo", base, url=str(origin))
    (work / "a.py").write_text("x = 2\n")
    (work / "new.py").write_text("y = 3\n")
    patch = workspace.diff(work)
    assert "-x = 1" in patch and "+x = 2" in patch
    assert "new.py" in patch


def test_db_roundtrip(tmp_path):
    conn = db.connect(tmp_path / "t.sqlite")
    db.insert_run(conn, run_id="r1", variant="B1", topology="B1", track="solo",
                  instance_id="i", started_at="now")
    db.insert_calls(conn, "r1", [dict(
        session_id="s", message_id="m", agent_id=None, role="solo", model="claude-opus-5-5",
        input_tokens=1, cache_write_5m=0, cache_write_1h=0, cache_read=0, output_tokens=1,
        prompt_tokens=1, long_context_tier=0, cost_usd=0.5)])
    db.update_run(conn, "r1", status="completed", cost_computed_usd=0.5)
    row = conn.execute("SELECT * FROM runs").fetchone()
    assert row["status"] == "completed" and row["smoke"] == 0
    assert conn.execute("SELECT count(*) FROM calls").fetchone()[0] == 1
