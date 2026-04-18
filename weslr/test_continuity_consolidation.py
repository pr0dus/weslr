from weslr.continuity_consolidation import consolidate, ConsolidationConfig


def test_consolidate_dedupes_and_trims():
    entries = [{"id": 1}, {"id": 1}, {"id": 2}]
    cfg = ConsolidationConfig(max_items=2, dedupe=True)
    out = consolidate(entries, cfg)
    assert len(out) == 2
    assert out[0]["id"] == 1
    assert out[1]["id"] == 2


def test_consolidate_drops_empty():
    entries = [{"id": 1}, {}, {"id": 2}]
    cfg = ConsolidationConfig(drop_empty=True)
    out = consolidate(entries, cfg)
    assert len(out) == 2


def test_consolidate_no_dedupe_allows_duplicates():
    entries = [{"id": 1}, {"id": 1}]
    cfg = ConsolidationConfig(dedupe=False)
    out = consolidate(entries, cfg)
    assert len(out) == 2
