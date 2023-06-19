"""Models for Splitwise data."""
from datetime import datetime
from decimal import Decimal

from dateutil.parser import isoparse
from pydantic import BaseModel

from ..util import to_decimal


class SwTransactionUser(BaseModel):
    """Model representing the user object inside a Splitwise transaction."""

    user_id: int
    net_balance: str

    def get_balance(self) -> Decimal:
        """Get the net balance for the user, as a Decimal."""
        return to_decimal(self.net_balance)


class SwTransaction(BaseModel):
    """Model representing a Splitwise transaction returned by the API."""

    id: int
    group_id: int | None
    description: str
    payment: bool
    cost: str
    date: str
    users: list[SwTransactionUser]

    def get_date(self) -> datetime:
        """Get the date of the transaction, as a datetime."""
        return isoparse(self.date)

    def get_user(self, user_id: int) -> SwTransactionUser:
        """Get the user object for the given id."""
        matching_users = [user for user in self.users if user.user_id == user_id]
        [matching_user] = matching_users
        return matching_user

    def __str__(self) -> str:
        return str(self.dict(include={"id", "description", "date", "cost"}))
