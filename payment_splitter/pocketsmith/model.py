from datetime import datetime, timezone
from decimal import Decimal

from dateutil.parser import isoparse
from pydantic import BaseModel

from ..util import to_decimal


class PsTransactionAccount(BaseModel):
    id: int


class PsTransaction(BaseModel):
    id: int
    payee: str
    date: str
    amount: float
    note: str | None
    labels: list[str]
    transaction_account: PsTransactionAccount

    def get_date(self) -> datetime:
        return isoparse(self.date).replace(tzinfo=timezone.utc)

    def get_amount(self) -> Decimal:
        return to_decimal(self.amount)

    def __str__(self) -> str:
        return str(self.dict(include={"id", "payee", "date", "amount"}))
