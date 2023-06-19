import logging

import requests

from .model import PsTransaction


class PsTransactionRetriever:
    def __init__(self, key: str) -> None:
        self._key = key

        self._logger = logging.getLogger("PsTransactionRetriever")
        self._logger.setLevel(logging.INFO)

    def get_settle_up_transactions(self) -> list[PsTransaction]:
        """Find and return the list of uncategorised settle-up transactions in Pocketsmith."""
        user_dict = self._get_current_user()
        user_id = user_dict["id"]

        transaction_dicts = self._get_transactions(
            user_id,
            {"uncategorised": 1, "search": "splitwise"},
        )
        transactions = [
            PsTransaction(**txn)
            for txn in transaction_dicts
            if "Splitwise" in txn["labels"]
        ]

        return transactions

    def _get_current_user(self) -> dict:
        """Get the current user from the Pocketsmith API."""
        url = "https://api.pocketsmith.com/v2/me"
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return response.json()

    def _get_transactions(self, user_id: int, params: dict = {}) -> list[dict]:
        """Get the list of transactions for the given user from the Pocketsmith API."""
        url = f"https://api.pocketsmith.com/v2/users/{user_id}/transactions"
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}

        data = []
        while url is not None:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data.extend(response.json())

            if "link" not in response.links:
                break

            url = response.links["next"]

        return data
