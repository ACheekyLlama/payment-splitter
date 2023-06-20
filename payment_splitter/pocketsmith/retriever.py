"""Module for retrieving transactions from Pocketsmith."""
import logging

from .client import PocketsmithClient
from .model import PsTransaction


class PocketsmithRetriever:
    """Class for retrieving transactions from Pocketsmith."""

    def __init__(self, client: PocketsmithClient) -> None:
        self._client = client

        self._logger = logging.getLogger("PocketsmithRetriever")
        self._logger.setLevel(logging.INFO)

    def get_settle_up_transactions(self) -> list[PsTransaction]:
        """Find and return the list of uncategorised settle-up transactions in Pocketsmith."""
        user_id = self._client.get_user_id()

        transaction_dicts = self._client.get_transactions(
            user_id,
            {"uncategorised": 1, "search": "splitwise"},
        )
        transactions = [
            PsTransaction(**txn)
            for txn in transaction_dicts
            if "Splitwise" in txn["labels"]
        ]

        return transactions
