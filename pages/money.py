import re
from decimal import Decimal

_MONEY = re.compile(r"\$(\d+(?:\.\d+)?)")


def parse_money(text: str) -> Decimal:
    """'$29.99' or 'Item total: $29.99' -> Decimal('29.99'). Decimal, so totals compare exactly."""
    match = _MONEY.search(text)
    if match is None:
        raise ValueError(f"no amount in {text!r}")
    return Decimal(match.group(1))
