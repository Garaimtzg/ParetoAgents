from pareto_agents.config import REPO_ROOT, load_experiment, load_variants
from pareto_agents.pricing import PriceTable


def test_ten_variants():
    variants = load_variants()
    assert len(variants) == 10
    assert len({v.id for v in variants}) == 10
    assert {"B1", "B2", "A1-SDK", "A1-CC", "A4-CC"} <= {v.id for v in variants}


def test_baselines_have_no_subagents_in_cc():
    for v in load_variants():
        if v.topology in {"B1", "B2"}:
            assert not v.subagents_enabled
            assert len(v.roles) == 1


def test_sdk_track_never_uses_cc_subagents():
    assert all(not v.subagents_enabled for v in load_variants() if v.track == "sdk")


def test_every_model_has_a_price():
    exp = load_experiment()
    prices = PriceTable.load(REPO_ROOT / exp["pricing_file"])
    for v in load_variants():
        for r in v.roles:
            assert r.model in prices.models, r.model


def test_baselines_are_single_track():
    assert {v.track for v in load_variants() if v.topology in {"B1", "B2"}} == {"solo"}


def test_same_roles_in_both_tracks():
    by_topo: dict[str, set] = {}
    for v in load_variants():
        by_topo.setdefault(v.topology, set()).add(v.roles)
    assert all(len(roles) == 1 for roles in by_topo.values())


def test_budget_caps_are_consistent():
    b = load_experiment()["budget_usd"]
    assert 0 < b["per_run_cap"] < b["phase2_pilot_cap"] < b["campaign_cap"]
