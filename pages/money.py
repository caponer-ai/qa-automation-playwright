import re

_MONEY = re.compile(r"\$(\d+(?:\.\d+)?)")


def parse_money(text: str) -> float:
    """'$29.99' or 'Item total: $29.99' -> 29.99"""
    match = _MONEY.search(text)
    if match is None:
        raise ValueError(f"no amount in {text!r}")
    return float(match.group(1))
