import pytest
from weslr.capability_intake import ingest_capabilities, validate_capability


def test_ingest_valid_capabilities():
    caps = [
        {"name": "execute", "description": "run commands", "risk": "high", "tags": ["system"]},
        {"name": "read", "description": "read files"},
    ]
    out = ingest_capabilities(caps)
    assert len(out) == 2
    assert out[0].risk == "high"
    assert out[1].risk == "medium"


def test_validate_rejects_missing_name():
    with pytest.raises(ValueError):
        validate_capability({"description": "run"})


def test_validate_rejects_invalid_risk():
    with pytest.raises(ValueError):
        validate_capability({"name": "execute", "description": "run", "risk": "extreme"})
