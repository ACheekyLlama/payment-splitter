from decimal import Decimal


def to_decimal(num: str | float) -> Decimal:
    return Decimal(num).quantize(Decimal("0.01"))
