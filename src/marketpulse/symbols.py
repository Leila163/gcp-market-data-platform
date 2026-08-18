def normalize_symbol(value: str) -> str:
    """Return a stock symbol without surrounding spaces and in uppercase."""
    return value.strip().upper()
