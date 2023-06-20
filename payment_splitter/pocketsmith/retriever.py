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
        """Get a list of the uncategorised settle-up transactions in Pocketsmith."""
        user_id = self._client.get_user().id

        transactions = self._client.get_transactions(
            user_id,
            {"uncategorised": 1, "search": "splitwise"},
        )
        settle_up_transactions = [
            txn for txn in transactions if "Splitwise" in txn.labels
        ]

        return settle_up_transactions
