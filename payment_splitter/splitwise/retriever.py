"""Module for retrieving transactions from the Splitwise API."""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable

from .client import SplitwiseClient
from .model import SwTransaction


class SplitwiseRetriever:
    """Class for retrieving transactions from Splitwise."""

    def __init__(self, client: SplitwiseClient) -> None:
        self._client = client

        self._logger = logging.getLogger("SplitwiseRetriever")
        self._logger.setLevel(logging.INFO)

    def get_matching_payment(
        self, amount: Decimal, timestamp: datetime, groups: list[int] = []
    ) -> SwTransaction | None:
        """Get the Splitwise payment from the API that matches the given amount and timestamp, and is in one of the provided groups."""
        transactions = self._client.get_all_transactions()
        if groups:
            transactions = [txn for txn in transactions if txn.group_id in groups]

        is_matching_payment = self._get_match_function(amount, timestamp)

        matching_payments = [txn for txn in transactions if is_matching_payment(txn)]

        if not matching_payments:
            return None

        [payment] = matching_payments
        return payment

    def _get_match_function(
        self, amount: Decimal, timestamp: datetime
    ) -> Callable[[SwTransaction], bool]:
        """Wrapper for a function which checks if a transaction is a payment and matches the given amount and timestamp."""
        user_id = self._client.get_user().id

        def is_matching(transaction: SwTransaction) -> bool:
            """Check if the given transaction is a payment and matches the given amount and timestamp."""
            payment_date = transaction.get_date()
            time_difference = payment_date - timestamp

            is_matching_amount = (
                transaction.get_user(user_id).get_balance() + amount
            ) == 0
            is_matching_timestamp = (
                timedelta(days=-2) < time_difference < timedelta(days=2)
            )

            return transaction.payment and is_matching_amount and is_matching_timestamp

        return is_matching
