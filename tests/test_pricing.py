import pytest

from pareto_agents.config import REPO_ROOT, load_experiment
from pareto_agents.pricing import PriceTable, Usage


@pytest.fixture(scope="module")
def prices() -> PriceTable:
    return PriceTable.load(REPO_ROOT / load_experiment()["pricing_file"])


def test_opus_one_mtok_of_each(prices):
    u = Usage(1_000_000, 1_000_000, 1_000_000, 1_000_000, 1_000_000)
    c = prices.cost("claude-opus-5-5", u)
    assert c.input == pytest.approx(4.0)
    assert c.cache_write == pytest.approx(5.0 + 8.0)
    assert c.cache_read == pytest.approx(0.20)
    assert c.output == pytest.approx(20.0)
    assert not c.long_context_tier


def test_sonnet_cache_read_is_010(prices):
    c = prices.cost("claude-sonnet-5-5", Usage(cache_read_tokens=1_000_000))
    assert c.cache_read == pytest.approx(0.10)


def test_haiku_threshold_is_inclusive_at_100k(prices):
    at = prices.cost("claude-haiku-5-5", Usage(input_tokens=100_000, output_tokens=1_000))
    assert not at.long_context_tier
    assert at.total == pytest.approx(100_000 * 0.10 / 1e6 + 1_000 * 0.50 / 1e6)


def test_haiku_cache_reads_count_toward_threshold(prices):
    # 10K nuevos + 95K de caché = 105K de prompt → tramo caro, salida incluida.
    u = Usage(input_tokens=10_000, cache_read_tokens=95_000, output_tokens=1_000)
    c = prices.cost("claude-haiku-5-5", u)
    assert c.long_context_tier
    assert c.input == pytest.approx(10_000 * 0.50 / 1e6)
    assert c.cache_read == pytest.approx(95_000 * 0.05 / 1e6)
    assert c.output == pytest.approx(1_000 * 2.50 / 1e6)


def test_haiku_long_tier_cache_writes(prices):
    u = Usage(cache_creation_5m_tokens=200_000)
    assert prices.cost("claude-haiku-5-5", u).cache_write == pytest.approx(200_000 * 0.625 / 1e6)


def test_opus_is_40x_haiku_on_input(prices):
    o = prices.cost("claude-opus-5-5", Usage(input_tokens=1000)).total
    h = prices.cost("claude-haiku-5-5", Usage(input_tokens=1000)).total
    assert o / h == pytest.approx(40)
