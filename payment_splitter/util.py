"""Module for simple utility functions."""
from decimal import Decimal


def to_decimal(num: str | float) -> Decimal:
    """Convert a str or float to a Decimal, rounding to the nearest hundredth."""
    return Decimal(num).quantize(Decimal("0.01"))
