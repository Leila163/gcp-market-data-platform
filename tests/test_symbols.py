import pytest

from marketpulse.symbols import normalize_symbol


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        (" lrcx ", "LRCX"),
        ("brk.b", "BRK.B"),
    ],
)
def test_normalize_symbol_returns_canonical_value(
    raw_value: str,
    expected: str,
) -> None:
    assert normalize_symbol(raw_value) == expected


@pytest.mark.parametrize(
    "raw_value",
    [
        "",
        "   ",
        "bad symbol",
        "$LRCX",
    ],
)
def test_normalize_symbol_rejects_invalid_values(raw_value: str) -> None:
    with pytest.raises(ValueError, match="valid stock symbol"):
        normalize_symbol(raw_value)
