from marketpulse.symbols import normalize_symbol


def test_normalize_symbol_strips_whitespace_and_uppercases() -> None:
    assert normalize_symbol(" lrcx ") == "LRCX"
