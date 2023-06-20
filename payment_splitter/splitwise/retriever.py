"""Module for retrieving transactions from the Splitwise API."""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable

from .client import SplitwiseClient
from .model import SwTransaction


class SplitwiseRetriever:
    """Class for retrieving transactions from Splitwise."""

    def __init__(self, client: SplitwiseClient, groups: list[int] = []) -> None:
        self._client = client
        self._groups = groups

        self._logger = logging.getLogger("SplitwiseRetriever")
        self._logger.setLevel(logging.INFO)

    def get_all_transactions(self) -> list[SwTransaction]:
        """Get all transactions for the current user from Splitwise."""

        transactions: list[SwTransaction] = []
        offset = 0
        while True:
            response_transactions = self._client.get_transactions(offset)

            if not response_transactions:
                break
            offset += len(response_transactions)
            transactions.extend(response_transactions)

        if self._groups:
            transactions = [txn for txn in transactions if txn.group_id in self._groups]

        return transactions

    def get_matching_payment(
        self, transactions: list[SwTransaction], amount: Decimal, timestamp: datetime
    ) -> SwTransaction | None:
        """Get the Splitwise payment from the list that matches the given amount and timestamp."""
        is_matching_payment = self._get_match_function(amount, timestamp)

        matching_payments = [txn for txn in transactions if is_matching_payment(txn)]

        if not matching_payments:
            return None

        [payment] = matching_payments
        return payment

    def _get_match_function(
        self, amount: Decimal, timestamp: datetime
    ) -> Callable[[SwTransaction], bool]:
        """Wrapper for a function which checks if transactions match the given amount and timestamp."""
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
