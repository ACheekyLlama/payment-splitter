"""Models for Pocketsmith data."""
from datetime import datetime, timezone
from decimal import Decimal

from dateutil.parser import isoparse
from pydantic import BaseModel

from ..util import to_decimal


class PsUser(BaseModel):
    """Model representing a user object returned from the Pocketsmith API."""

    id: int


class PsTransactionAccount(BaseModel):
    """Model representing a transaction account object returned from the Pocketsmith API."""

    id: int


class PsTransaction(BaseModel):
    """Model representing a transaction object returned from the Pocketsmith API."""

    id: int
    payee: str
    date: str
    amount: float
    note: str | None
    labels: list[str]
    transaction_account: PsTransactionAccount

    def get_date(self) -> datetime:
        """Get the date for this transaction as a timezone-aware datetime object."""
        return isoparse(self.date).replace(tzinfo=timezone.utc)

    def get_amount(self) -> Decimal:
        """Get the amount of this transaction as decimal with two decimal places."""
        return to_decimal(self.amount)

    def __str__(self) -> str:
        """User-facing string representation."""
        return str(self.dict(include={"id", "payee", "date", "amount"}))
