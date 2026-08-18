import re

_SYMBOL_PATTERN = re.compile(
    r"[A-Z][A-Z0-9]*(?:[.-][A-Z0-9]+)*",
)


def normalize_symbol(value: str) -> str:
    """Return a validated stock symbol in its canonical uppercase form."""
    symbol = value.strip().upper()

    if len(symbol) > 20 or _SYMBOL_PATTERN.fullmatch(symbol) is None:
        raise ValueError(f"{value!r} is not a valid stock symbol")

    return symbol
