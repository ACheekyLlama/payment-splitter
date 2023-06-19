"""Module for retrieving transactions from the Splitwise API."""
import logging
from datetime import datetime, timedelta
from decimal import Decimal

import requests

from .client import PocketsmithClient
from .model import SwTransaction


class SwTransactionRetriever:
    """Class for retrieving transactions from the Splitwise API."""

    def __init__(self, client: PocketsmithClient, groups: list = []) -> None:
        self._client = client
        self._groups = groups

        self._logger = logging.getLogger("SwTransactionRetriever")
        self._logger.setLevel(logging.INFO)

    def get_all_transactions(self) -> list[SwTransaction]:
        """Fetch and return all transactions from the Splitwise API."""
        headers = {"Authorization": f"Bearer {self._key}", "accept": "application/json"}

        transactions_dicts = []
        offset = 0
        while True:
            transaction_response = requests.get(
                "https://secure.splitwise.com/api/v3.0/get_expenses",
                headers=headers,
                params={"offset": offset},
            )
            transaction_response.raise_for_status()
            response_dict = transaction_response.json()

            if not response_dict["expenses"]:
                break
            offset += len(response_dict["expenses"])
            transactions_dicts.extend(response_dict["expenses"])

        transactions = [SwTransaction(**txn) for txn in transactions_dicts]
        if self._groups:
            transactions = [x for x in transactions if x.group_id in self._groups]

        return transactions

    def get_matching_payment(
        self, transactions: list[SwTransaction], amount: Decimal, timestamp: datetime
    ) -> SwTransaction | None:
        """Get the Splitwise payment from the list that matches the given amount and timestamp."""
        matching_payments = [
            txn
            for txn in transactions
            if txn.payment and self._is_matching(txn, amount, timestamp)
        ]

        if not matching_payments:
            return None

        [payment] = matching_payments
        return payment

    # TODO: make this a wrapper method, get it as a matcher above and then use it.
    def _is_matching(
        self, payment: SwTransaction, amount: Decimal, timestamp: datetime
    ) -> bool:
        """Check if the given payment matches the given amount and timestamp."""
        payment_date = payment.get_date()
        time_difference = payment_date - timestamp
        user_id = (
            self._client.get_user_id()
        )  # TODO: this will be slow, pass this in or something

        is_matching_amount = (payment.get_user(user_id).get_balance() + amount) == 0
        is_matching_timestamp = timedelta(days=-2) < time_difference < timedelta(days=2)

        return is_matching_amount and is_matching_timestamp
