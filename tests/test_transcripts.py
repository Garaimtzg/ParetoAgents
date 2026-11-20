"""Basado en una sesión real de Claude Code 2.1.329 (Haiku + un subagente "reader")."""

import json
from pathlib import Path

import pytest

from pareto_agents.config import REPO_ROOT, load_experiment
from pareto_agents.pricing import PriceTable
from pareto_agents.transcripts import find_session_file, reconcile, session_calls

FIX = Path(__file__).parent / "fixtures" / "session"
SID = "bb93eab8-6613-43f8-8643-ebb6c7bf099c"


@pytest.fixture(scope="module")
def calls():
    prices = PriceTable.load(REPO_ROOT / load_experiment()["pricing_file"])
    return session_calls(FIX / f"{SID}.jsonl", prices, main_role="solo")


@pytest.fixture(scope="module")
def result():
    return json.loads((FIX / "result.json").read_text())


def test_roles_main_and_subagent(calls):
    roles = [c["role"] for c in calls]
    assert roles.count("solo") == 3
    assert roles.count("reader") == 2  # agentType de meta.json
    assert all(c["agent_id"] for c in calls if c["role"] == "reader")


def test_tokens_match_claude_code_totals(calls, result):
    # Nuestro recuento por modelo cuadra EXACTAMENTE con modelUsage de Claude Code.
    assert reconcile(calls, result["modelUsage"]) == {}


def test_cost_matches_claude_code(calls, result):
    ours = sum(c["cost_usd"] for c in calls)
    assert ours == pytest.approx(result["total_cost_usd"], rel=0.01)


def test_cache_ttl_split(calls):
    main = [c for c in calls if c["role"] == "solo"]
    sub = [c for c in calls if c["role"] == "reader"]
    assert sum(c["cache_write_1h"] for c in main) > 0 and sum(c["cache_write_5m"] for c in main) == 0
    assert sum(c["cache_write_5m"] for c in sub) > 0 and sum(c["cache_write_1h"] for c in sub) == 0


def test_duplicate_message_lines_counted_once(tmp_path, calls):
    lines = (FIX / f"{SID}.jsonl").read_text().splitlines()
    (tmp_path / "dup.jsonl").write_text("\n".join(lines + lines[:1]) + "\n")
    prices = PriceTable.load(REPO_ROOT / load_experiment()["pricing_file"])
    assert len(session_calls(tmp_path / "dup.jsonl", prices, "solo")) == 3


def test_find_session_file(tmp_path):
    (tmp_path / "-some-project").mkdir()
    f = tmp_path / "-some-project" / "abc.jsonl"
    f.write_text("")
    assert find_session_file("abc", root=tmp_path) == f
    with pytest.raises(FileNotFoundError):
        find_session_file("nope", root=tmp_path)
